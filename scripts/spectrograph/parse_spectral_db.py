import argparse
import csv
import ast
import os

def extract_sce_to_spd(input_csv, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            id_ = row.get("ID", "unknown").strip()
            name = row.get("Name", "noname").strip().replace(" ", "_").replace("/", "_")
            filename = f"{id_}_{name}_sce.spd"
            filepath = os.path.join(output_folder, filename)

            sce_data = row.get("SCEMeasures", "").strip()
            try:
                sce_dict = ast.literal_eval(sce_data)
                if not isinstance(sce_dict, dict):
                    raise ValueError("SCEMeasures is not a dictionary")

                with open(filepath, "w", encoding='utf-8') as f:
                    f.write(f"# {filename}\n")
                    for wavelength, irradiance in sorted(sce_dict.items(), key=lambda x: float(x[0])):
                        f.write(f"{wavelength} {irradiance}\n")

                print(f"Saved: {filepath}")
            except Exception as e:
                print(f"Skipping row {id_} ({name}): {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract SCEMeasures and save as .spd files.")
    parser.add_argument("input_csv", help="Path to the input CSV file.")
    parser.add_argument("output_folder", help="Directory to save the .spd output files.")
    args = parser.parse_args()

    extract_sce_to_spd(args.input_csv, args.output_folder)
