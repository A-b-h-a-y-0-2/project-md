# Project-MD

Simple utility to upload files into a local uploads folder, compute a SHA-256 hash for each file, and record file metadata in a MongoDB collection.

## What exists so far

- `upload_file.py` — main script. Copies the provided file into the `UPLOAD_DIR`, computes its SHA-256 hash, and inserts a document into the `documents` collection in MongoDB with fields: `user_id`, `filename`, `file_path`, `file_hash`, `upload_timestamp`, `status`, `metadata`.
- `test_mongo.py` — helper/test script (present in the workspace).
- `data/uploads/` — example upload directory (files copied here during runs).

## Requirements

- Python 3.8+
- Packages:
  - `pymongo`
  - `python-dotenv`

Install dependencies:

```bash
python -m pip install pymongo python-dotenv
```

## Configuration

The project uses environment variables. Create a `.env` file in the project root with at least the following values:

```
MONGO_URI=mongodb://localhost:27017
DB_NAME=project_md
UPLOAD_DIR=data/uploads
```

Adjust `MONGO_URI` and `DB_NAME` for your MongoDB instance.

## Usage

Run the uploader with the file path as an argument:

```bash
python upload_file.py /path/to/file.pdf
```

Behavior:
- The file is copied into `UPLOAD_DIR` (created if missing).
- A SHA-256 hash is computed for the copied file.
- A document with the file metadata is inserted into the `documents` collection.
- The script prints the inserted document ID and the file's hash.

## Notes

- Ensure MongoDB is accessible using `MONGO_URI` before running the script.
- `upload_file.py` currently uses a hard-coded `user_id` value (`user_123`); change as needed.

## License

MIT

## Contact

Project generated locally. No further contact information included.
