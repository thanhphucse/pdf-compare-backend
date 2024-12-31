import cv2
import numpy as np
import os
from skimage.metrics import structural_similarity as ssim
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


@csrf_exempt
def compare_images(request):
    if request.method == "POST":
        file1 = request.FILES.get('file1')
        file2 = request.FILES.get('file2')

        if not file1 or not file2:
            return JsonResponse({"error": "Both files are required."}, status=400)

        try:
            # Save files temporarily
            temp_dir = 'temp_files'
            os.makedirs(temp_dir, exist_ok=True)
            file1_path = os.path.join(temp_dir, file1.name)
            file2_path = os.path.join(temp_dir, file2.name)

            with open(file1_path, 'wb') as f1, open(file2_path, 'wb') as f2:
                f1.write(file1.read())
                f2.write(file2.read())

            # Process and compare images
            result_image_path = process_and_compare(file1_path, file2_path)
            
            # Clean up temporary input images
            os.remove(file1_path)
            os.remove(file2_path)

            # Return highlighted image URL
            return JsonResponse({
                "highlighted_differences_url": f"{settings.MEDIA_URL}{result_image_path}"
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method."}, status=405)

def get_bounding_boxes(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply adaptive thresholding to enhance text
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 15
    )
    
    # Perform morphological operations to connect components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))  # Adjust kernel size as needed
    dilated = cv2.dilate(thresh, kernel, iterations=4)

    # Find contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Merge nearby contours into a single bounding box
    bounding_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w > 1 and h > 1:  # Filter small boxes (adjust thresholds as needed)
            bounding_boxes.append((x, y, w, h))
    
    # Merge overlapping bounding boxes
    bounding_boxes = merge_overlapping_boxes(bounding_boxes)
    return bounding_boxes

def merge_overlapping_boxes(boxes, overlap_threshold=0.3):
    """
    Merges overlapping or close bounding boxes.
    """
    if not boxes:
        return []
    
    # Sort boxes by x-coordinates
    boxes = sorted(boxes, key=lambda b: b[0])
    
    merged_boxes = []
    current_box = boxes[0]
    
    for next_box in boxes[1:]:
        x1, y1, w1, h1 = current_box
        x2, y2, w2, h2 = next_box
        
        # Calculate the overlap
        if (x2 < x1 + w1 + overlap_threshold * w1) and (y2 < y1 + h1 + overlap_threshold * h1):
            # Merge boxes
            x = min(x1, x2)
            y = min(y1, y2)
            w = max(x1 + w1, x2 + w2) - x
            h = max(y1 + h1, y2 + h2) - y
            current_box = (x, y, w, h)
        else:
            # Save the current box and move to the next
            merged_boxes.append(current_box)
            current_box = next_box
    
    # Add the last box
    merged_boxes.append(current_box)
    return merged_boxes

def process_and_compare(img1_path, img2_path):
    # Load the two images
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1 is None or img2 is None:
        raise ValueError("One or both images are invalid or corrupted.")

    # Step 1: Identify Objects and Bounding Boxes
    bounding_boxes1 = get_bounding_boxes(img1)
    bounding_boxes2 = get_bounding_boxes(img2)

    # Ensure at least one bounding box exists in both images
    if not bounding_boxes1 or not bounding_boxes2:
        raise ValueError("No significant objects detected in one or both images.")

    # Use the largest bounding box (assume main object)
    x1, y1, w1, h1 = max(bounding_boxes1, key=lambda b: b[2] * b[3])
    x2, y2, w2, h2 = max(bounding_boxes2, key=lambda b: b[2] * b[3])

    # Step 2: Resize Images to Fit Identified Objects
    padding = 0
    crop1 = img1[max(0, y1-padding):y1+h1+padding, max(0, x1-padding):x1+w1+padding]
    crop2 = img2[max(0, y2-padding):y2+h2+padding, max(0, x2-padding):x2+w2+padding]

    height, width = min(crop1.shape[0], crop2.shape[0]), min(crop1.shape[1], crop2.shape[1])
    crop1_resized = cv2.resize(crop1, (width, height))
    crop2_resized = cv2.resize(crop2, (width, height))

    # Step 3: Convert Images to a Feature Representation Using SIFT
    sift = cv2.SIFT_create()
    keypoints1, descriptors1 = sift.detectAndCompute(crop1_resized, None)
    keypoints2, descriptors2 = sift.detectAndCompute(crop2_resized, None)

    # Step 4: Use Homography to Align Images
    matcher = cv2.BFMatcher()
    matches = matcher.knnMatch(descriptors1, descriptors2, k=2)

    # Apply ratio test
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            good_matches.append(m)

    if len(good_matches) < 4:
        raise ValueError("Two images are very different.")

    src_pts = np.float32([keypoints1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([keypoints2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    # Warp the second image to align with the first
    crop2_aligned = cv2.warpPerspective(crop2_resized, H, (width, height))

    # Step 5: Compare Images
    crop1_gray = cv2.cvtColor(crop1_resized, cv2.COLOR_BGR2GRAY)
    crop2_gray = cv2.cvtColor(crop2_aligned, cv2.COLOR_BGR2GRAY)

    # Create a directory to save the images (if it doesn't exist)
    debug_dir = os.path.join(settings.MEDIA_ROOT, 'debug_images')  # Adjust path as needed
    os.makedirs(debug_dir, exist_ok=True)
    cv2.imwrite(os.path.join(debug_dir, 'crop1_resized.jpg'), crop1_resized)
    cv2.imwrite(os.path.join(debug_dir, 'crop2_resized.jpg'), crop2_resized) 

    # Compute the absolute difference between the two images
    # diff = cv2.absdiff(crop1_gray, crop2_gray)
    diff = cv2.absdiff(crop1_resized, crop2_resized)

    # Threshold the difference image to create a binary mask for significant differences
    _, diff_mask = cv2.threshold(diff, 100, 255, cv2.THRESH_BINARY)

    # Highlight differences in magenta on the first image
    highlighted = crop2_resized.copy()
    magenta = np.zeros_like(highlighted)
    magenta[:, :] = (255, 0, 255)  # Magenta color (BGR format)
    highlighted[diff_mask != 0] = magenta[diff_mask != 0]

    # Step 6: Save the Result Image
    result_image_path = os.path.join(settings.MEDIA_ROOT, "highlighted_differences.png")
    cv2.imwrite(result_image_path, highlighted)

    return "highlighted_differences.png"
