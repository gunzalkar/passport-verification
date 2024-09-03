import csv
import json
import traceback
from typing import Any, Optional, Tuple, Set

import cv2
import numpy as np
from fastmrz import FastMRZ
from mrz.checker.td3 import TD3CodeChecker


def load_country_codes_from_file(file_path: str) -> Set[str]:
	valid_codes = set()
	try:
		with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
			csv_reader = csv.DictReader(csvfile)
			for row in csv_reader:
				valid_codes.add(row["alpha-3"])
	except Exception as e:
		print(f"Error loading country codes: {e}")
	return valid_codes


def is_valid_country_code(country_code: str, valid_codes: Set[str]) -> bool:
	return country_code.upper() in valid_codes


valid_country_codes = load_country_codes_from_file("All data.csv")


def calculate_check_digit(data):
	# Weights for the MRZ check digit calculation
	weight = [7, 3, 1]
	total = 0
	for i, char in enumerate(data):
		if char.isdigit():
			value = int(char)
		elif char.isalpha():
			value = ord(char) - ord("A") + 10
		elif char == "<":
			value = 0
		else:
			raise ValueError("Invalid character in MRZ data")
		total += value * weight[i % 3]
	return str(total % 10)


def validate_mrz_field(mrz_field):
	# Extract data and check digit
	data = mrz_field[:-1]
	expected_check_digit = mrz_field[-1]

	# Calculate the check digit
	calculated_check_digit = calculate_check_digit(data)
	# Return if calculated check digit matches expected check digit
	return calculated_check_digit == expected_check_digit


def reformat_date(date_str):
	if len(date_str) != 10:
		raise ValueError("Date string must be in YYYY-MM-DD format")
	year, month, day = date_str.split("-")
	return f"{day}.{month}.{year}"


def detect_and_crop_face(image, padding_percent=0.2):
	face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
	gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
	if len(faces) > 0:
		(x, y, w, h) = faces[0]
		x_padding = int(w * padding_percent)
		y_padding = int(h * padding_percent)
		x_start = max(x - x_padding, 0)
		y_start = max(y - y_padding, 0)
		x_end = min(x + w + x_padding, image.shape[1])
		y_end = min(y + h + y_padding, image.shape[0])
		face_image = image[y_start:y_end, x_start:x_end]
		return face_image
	return None


def crop_mrz(image):
	height, width = image.shape[:2]
	mrz_height = int(height * 0.2)
	cropped_image = image[height - mrz_height : height, 0:width]
	return cropped_image


def validate_full_mrz(mrz: str) -> bool:
	if not mrz or "\n" not in mrz or len(mrz.split("\n")) != 2:
		return False

	line1, line2 = mrz.split("\n")

	if len(line1) != 44 or len(line2) != 44:
		return False

	if not all(c.isalnum() or c == "<" for c in line1 + line2):
		return False

	return True


def get_info(img_path: str) -> Tuple[dict[str, Any], Optional[np.ndarray], Optional[np.ndarray]]:
	try:
		image = cv2.imread(img_path, cv2.IMREAD_COLOR)
		print(img_path)
		if image is None:
			return {"error": "Could not read image, please check the path."}, None, None

		# fast_mrz = FastMRZ(tesseract_path=r"/opt/homebrew/bin/tesseract")  # Default path in Mac
		fast_mrz = FastMRZ(tesseract_path=r"/usr/bin/tesseract")  # Default path in Linux
		passport_mrz = fast_mrz.get_mrz(img_path)
		raw_mrz = fast_mrz.get_raw_mrz(img_path)

		print(f"The text data is {raw_mrz}")
		if passport_mrz["status"] != "SUCCESS":
			return {"error": "Couldn't extract data from image. Try a clearer image."}, None, None
		td3_check = TD3CodeChecker(str(raw_mrz), check_expiry=True)

		fields = td3_check.fields()

		invalid_fields = [field[0] for field in td3_check.report.falses] if td3_check.report.falses else []
		print("Fields:", fields)
		print("Invalid Fields:", invalid_fields)

		def check_falses(key_words):
			for invalid_field in invalid_fields:
				if key_words in invalid_field:
					return False
			return True

		fields_dict = {
			"full_mrz": {
				"value": raw_mrz,
				"status": validate_mrz_field(passport_mrz["document_number"])
				and is_valid_country_code(passport_mrz["country_code"], valid_country_codes),
			},
			"mrz_birth_date": {
				"value": reformat_date(passport_mrz["date_of_birth"]),
				"status": check_falses("birth"),
			},
			"mrz_cd_birth_date": {
				"value": fields.birth_date_hash,
				"status": check_falses("birth date hash"),
			},
			"mrz_cd_composite": {
				"value": fields.final_hash,
				"status": check_falses("final hash"),
			},
			"mrz_cd_expiry_date": {
				"value": fields.expiry_date_hash,
				"status": check_falses("expiry date hash"),
			},
			"mrz_cd_number": {
				"value": fields.document_number_hash,
				"status": check_falses("document number hash"),
			},
			"mrz_cd_opt_data_2": {
				"value": fields.optional_data_hash,
				"status": validate_mrz_field(fields.optional_data + fields.optional_data_hash),
			},
			"mrz_doc_type_code": {
				"value": passport_mrz["document_type"],
				"status": check_falses("document type"),
			},
			"mrz_expiry_date": {
				"value": reformat_date(passport_mrz["date_of_expiry"]),
				"status": check_falses("expiry date"),
			},
			"mrz_gender": {
				"value": passport_mrz["sex"],
				"status": check_falses("sex"),
			},
			"mrz_issuer": {
				"value": passport_mrz["country_code"],
				"status": check_falses("nationality")
				and is_valid_country_code(passport_mrz["country_code"], valid_country_codes),
			},
			"mrz_last_name": {
				"value": passport_mrz["surname"],
				"status": True,
			},
			"mrz_line1": {
				"value": raw_mrz.split("\n")[0] if "\n" in raw_mrz else "",
				"status": validate_mrz_field(passport_mrz["document_number"])
				and is_valid_country_code(passport_mrz["country_code"], valid_country_codes),
			},
			"mrz_line2": {
				"value": raw_mrz.split("\n")[1] if "\n" in raw_mrz else "",
				"status": validate_mrz_field(passport_mrz["document_number"])
				and is_valid_country_code(passport_mrz["country_code"], valid_country_codes),
			},
			"mrz_name": {
				"value": passport_mrz["given_name"],
				"status": True,
			},
			"mrz_nationality": {
				"value": passport_mrz["nationality"],
				"status": check_falses("nationality")
				and is_valid_country_code(passport_mrz["nationality"], valid_country_codes),
			},
			"mrz_number": {
				"value": passport_mrz["document_number"],
				"status": check_falses("document number") and validate_mrz_field(fields.document_number),
			},
			"mrz_opt_data_2": {
				"value": fields.optional_data,
				"status": True,
			},
		}

		face_img = detect_and_crop_face(image)
		mrz_code_img = crop_mrz(image)

		print("JSON:")
		print(json.dumps(passport_mrz, indent=4))

		print("\nTEXT:")
		print(raw_mrz)
		print(json.dumps(fields_dict, indent=4))
		return fields_dict, face_img, mrz_code_img

	except Exception as e:
		print(traceback.format_exc())
		return {"error": f"Failed to process image: {str(e)}"}, None, None
