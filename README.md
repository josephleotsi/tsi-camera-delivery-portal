# TSI Camera Portal - Online Deployment

This version uses Supabase PostgreSQL + private Supabase Storage instead of local SQLite/files.

## 1. Create Supabase project
1. Create a Supabase project.
2. Open **SQL Editor**, paste `schema.sql`, and run it.
3. In **Storage**, create a private bucket named `order-documents`.
4. Copy the Project URL and service-role key from Supabase project settings.

## 2. Local online-version test
1. Copy `.streamlit/secrets.example.toml` to `.streamlit/secrets.toml`.
2. Fill in the project URL and service-role key.
3. Run:
   `py -3.13 -m venv .venv`
   `.venv\Scripts\activate`
   `pip install -r requirements.txt`
   `streamlit run app.py`

## 3. GitHub
Create a private repository and upload only the files in this folder.
Do not upload `.streamlit/secrets.toml`, a local database, customer PDFs, or `.venv`.

## 4. Streamlit Community Cloud
1. Create an app from the private GitHub repository.
2. Entry point: `app.py`.
3. In Advanced settings choose Python 3.13.
4. Paste the same secret values into Streamlit Secrets.
5. Deploy and configure the app as private/viewer-restricted.

## Security notes
- The service-role key stays in Streamlit Secrets and must never be committed to GitHub.
- The team still signs in to this portal using accounts created by Finance Admin.
- The storage bucket must remain private.
- Finance Admin performs all writes; Team Viewer has read/download functions only.
