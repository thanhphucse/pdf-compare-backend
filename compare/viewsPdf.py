import cv2
import numpy as np
import fitz
import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

def pdf_to_image(pdf_path, page_number, zoom=3):
    pdf_document = fitz.open(pdf_path)
    if page_number >= len(pdf_document):
        return None
    page = pdf_document[page_number]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return img

def visualize_differences(image1, image2_aligned):
    diff = cv2.absdiff(image1, image2_aligned)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, diff_thresh = cv2.threshold(diff_gray, 150, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(diff_thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    highlighted_img = image1.copy()
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        region1 = image1[y:y+h, x:x+w]
        region2 = image2_aligned[y:y+h, x:x+w]
        mean1 = np.mean(region1)
        mean2 = np.mean(region2)
        color = (255, 0, 0) if mean1 < mean2 else (0, 255, 0)
        cv2.drawContours(highlighted_img, [contour], -1, color, 2)
    return highlighted_img

def images_to_pdf(image_list, output_pdf_path):
    pdf_document = fitz.open()
    for img_path in image_list:
        img = fitz.open(img_path)
        pdf_bytes = img.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdf_bytes)
        pdf_document.insert_pdf(img_pdf)
    pdf_document.save(output_pdf_path)
    pdf_document.close()

@csrf_exempt
def compare_pdfs(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method."}, status=405)

    file1 = request.FILES.get('file1')
    file2 = request.FILES.get('file2')

    if not file1 or not file2:
        return JsonResponse({"error": "Both files are required."}, status=400)

    try:
        # Save uploaded files temporarily
        temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp_files')
        os.makedirs(temp_dir, exist_ok=True)
        file1_path = os.path.join(temp_dir, file1.name)
        file2_path = os.path.join(temp_dir, file2.name)

        with open(file1_path, 'wb') as f:
            f.write(file1.read())
        with open(file2_path, 'wb') as f:
            f.write(file2.read())

        # Generate the output path
        output_pdf_path = os.path.join(settings.MEDIA_ROOT, 'Highlighted_Output.pdf')

        # Compare PDFs
        pdf1 = fitz.open(file1_path)
        pdf2 = fitz.open(file2_path)

        output_images = []

        for page_number in range(min(len(pdf1), len(pdf2))):
            try:
                image1 = pdf_to_image(file1_path, page_number)
                image2 = pdf_to_image(file2_path, page_number)

                if image1 is None or image2 is None:
                    continue

                gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

                orb = cv2.ORB_create(
                    nfeatures=10000, scaleFactor=1.1, nlevels=32,
                    edgeThreshold=31, firstLevel=0, WTA_K=2, 
                    patchSize=31, fastThreshold=1
                )

                kp1, des1 = orb.detectAndCompute(gray1, None)
                kp2, des2 = orb.detectAndCompute(gray2, None)

                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                matches = bf.match(des1, des2)
                matches = sorted(matches, key=lambda x: x.distance, reverse=False)

                src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

                H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC)
                height, width, _ = image1.shape
                image2_aligned = cv2.warpPerspective(image2, H, (width, height))

                diff = cv2.absdiff(image1, image2_aligned)
                diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
                _, diff_thresh = cv2.threshold(diff_gray, 150, 255, cv2.THRESH_BINARY)

                if cv2.countNonZero(diff_thresh) > 0:
                    highlighted_image = visualize_differences(image1, image2_aligned)
                    highlighted_image = cv2.cvtColor(highlighted_image, cv2.COLOR_BGR2RGB)
                    # Save intermediate images
                    output_image_path = os.path.join(temp_dir, f"highlighted_page_{page_number + 1}.png")
                    cv2.imwrite(output_image_path, highlighted_image)
                    output_images.append(output_image_path)
                    
                else:
                    print(f"Page {page_number + 1} has no differences.")
            except Exception as e:
                print(f"Error processing page {page_number + 1}: {e}")

        if output_images:
            images_to_pdf(output_images, output_pdf_path)
            response_data = {
                "highlighted_pdf_url": f"{settings.MEDIA_URL}Highlighted_Output.pdf"
            }
        else:
            response_data = {"message": "No differences found."}

        # Cleanup
        for temp_file in [file1_path, file2_path]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    # Log or handle the exception
                    print(f"Error removing file {temp_file}: {e}")

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
