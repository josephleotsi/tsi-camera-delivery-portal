import streamlit as st
from supabase import create_client
c=create_client(st.secrets['SUPABASE_URL'],st.secrets['SUPABASE_SERVICE_ROLE_KEY'])
try:
    c.storage.create_bucket('order-documents',options={'public':False})
    print('Private bucket order-documents created.')
except Exception as e:
    print('Bucket may already exist:',e)
