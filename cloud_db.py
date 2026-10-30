import bcrypt
import streamlit as st
from supabase import create_client

@st.cache_resource
def client():
    return create_client(st.secrets['SUPABASE_URL'], st.secrets['SUPABASE_SERVICE_ROLE_KEY'])

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def user_count():
    res=client().table('portal_users').select('id',count='exact').limit(1).execute()
    return res.count or 0

def create_user(email,name,password,role,actor_id=None):
    row={'email':email.strip().lower(),'full_name':name.strip(),'password_hash':hash_password(password),'role':role,'active':True}
    created=client().table('portal_users').insert(row).execute().data[0]
    if actor_id: audit(actor_id,'USER_CREATED',f"{row['email']} as {role}")
    return created

def authenticate(email,password):
    data=client().table('portal_users').select('*').eq('email',email.strip().lower()).eq('active',True).limit(1).execute().data
    return data[0] if data and verify_password(password,data[0]['password_hash']) else None

def audit(user_id,action,details='',order_id=None):
    client().table('audit_log').insert({'user_id':user_id,'order_id':order_id,'action':action,'details':details}).execute()

def clearance(order):
    contract=float(order.get('contract_amount') or 0); advance=float(order.get('advance_received') or 0); balance=float(order.get('balance_received') or 0)
    advance_required=contract*.5; balance_required=contract-advance_required; total=advance+balance
    if contract>0 and advance>=advance_required and balance>=balance_required and total>=contract: status='CLEARED FOR DELIVERY'
    elif advance>=advance_required: status='WAITING FOR 50% BALANCE'
    else: status='WAITING FOR 50% ADVANCE'
    return advance_required,balance_required,total,max(contract-total,0),status
