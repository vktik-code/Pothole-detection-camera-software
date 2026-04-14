import os
import xml.etree.ElementTree as ET

# -------- CONFIGURATION --------
xml_dir = "dataset/labels/train"   # Folder with your Pascal VOC XML files
yolo_dir = "dataset/labels/trainyolo"  # Folder to save YOLO .txt files
class_name = "pothole"  # class in your XML
class_id = 0  # ID in data.yaml
# -------------------------------

os.makedirs(yolo_dir, exist_ok=True)

for xml_file in os.listdir(xml_dir):
    if not xml_file.endswith(".xml"):
        continue

    tree = ET.parse(os.path.join(xml_dir, xml_file))
    root = tree.getroot()

    # Get image size
    size = root.find("size")
    img_width = int(size.find("width").text)
    img_height = int(size.find("height").text)

    yolo_lines = []

    # Loop over all objects
    for obj in root.findall("object"):
        name = obj.find("name").text
        if name != class_name:
            continue  # skip other classes if any

        bndbox = obj.find("bndbox")
        xmin = float(bndbox.find("xmin").text)
        ymin = float(bndbox.find("ymin").text)
        xmax = float(bndbox.find("xmax").text)
        ymax = float(bndbox.find("ymax").text)

        # Convert to YOLO format (normalized)
        x_center = (xmin + xmax) / 2 / img_width
        y_center = (ymin + ymax) / 2 / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height

        yolo_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

    # Write YOLO .txt file
    txt_file = os.path.join(yolo_dir, os.path.splitext(xml_file)[0] + ".txt")
    with open(txt_file, "w") as f:
        f.write("\n".join(yolo_lines))

print("Conversion completed!")