import streamlit as st
import pandas as pd
from uuid import uuid4
from cloud_db import client,user_count,create_user,authenticate,audit,clearance

st.set_page_config(page_title='TSI Camera Control',page_icon='📷',layout='wide',initial_sidebar_state='expanded')
st.markdown('''<style>
:root{--bg:#161B22;--side:#1C222B;--card:#26313D;--card2:#222B36;--border:#425066;--text:#F2F5F9;--muted:#AAB5C3;--blue:#4C8BF5}
html,body,[data-testid="stAppViewContainer"],.stApp{background:var(--bg);color:var(--text)}
[data-testid="stSidebar"]{background:var(--side);border-right:1px solid var(--border)}
[data-testid="stHeader"]{background:rgba(22,27,34,.96);border-bottom:1px solid var(--border)}
.block-container{max-width:1500px;padding-top:2rem}h1,h2,h3,p,label,[data-testid="stMarkdownContainer"]{color:var(--text)}
.portal-hero{display:flex;justify-content:space-between;align-items:center;padding:1.5rem 1.7rem;margin-bottom:1.7rem;background:linear-gradient(120deg,#26354C,#202B39 62%,#25466D);border:1px solid #43536A;border-radius:16px}
.eyebrow,.section{font-size:.7rem;font-weight:800;letter-spacing:.14em;color:#70A4FF}.title{font-size:1.7rem;font-weight:760;margin:.35rem 0}.sub{color:#B7C2CF}.live{padding:.5rem .7rem;border-radius:999px;background:#1D2733;border:1px solid #425066;font-size:.7rem;font-weight:800}.live b{display:inline-block;width:7px;height:7px;border-radius:50%;background:#2EA043;margin-right:.4rem}
[data-testid="stForm"],[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card2);border:1px solid var(--border);border-radius:14px;padding:1rem}
[data-testid="stMetric"]{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:1rem}.stCaption,small{color:var(--muted)!important}
.stTextInput input,.stNumberInput input,.stTextArea textarea,[data-baseweb="select"]>div{background:#29323E!important;color:var(--text)!important;border-color:#4B5A6D!important}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{background:var(--blue);color:white;border:0;border-radius:9px;font-weight:700;min-height:2.55rem}
.order{display:grid;grid-template-columns:2fr 1fr 1fr 1.1fr;gap:1rem;align-items:center;background:#242E3A;border:1px solid #3E4D60;padding:1rem 1.2rem;border-radius:12px;margin:.7rem 0}.order strong{color:white}.meta{color:#A9B5C4;font-size:.77rem}.money span{display:block;color:#9BA8B8;font-size:.66rem;letter-spacing:.08em}.badge{padding:.33rem .5rem;border-radius:6px;font-size:.65rem;font-weight:800}.red{color:#FFAAA5;border:1px solid #8C4242;background:#3C272A}.amber{color:#F1C96B;border:1px solid #806A31;background:#383126}.green{color:#75D48A;border:1px solid #397847;background:#243A2A}
#MainMenu,footer,[data-testid="stToolbar"]{visibility:hidden}@media(max-width:900px){.order{grid-template-columns:1fr 1fr}.order .main{grid-column:1/-1}}
</style>''',unsafe_allow_html=True)

def require_admin():
    if st.session_state.user['role']!='FINANCE_ADMIN': st.error('Finance Admin access required.'); st.stop()
def logout(): st.session_state.pop('user',None); st.rerun()
def order_rows(search=''):
    q=client().table('orders').select('*').order('updated_at',desc=True)
    rows=q.execute().data
    if search:
        k=search.lower(); rows=[r for r in rows if k in str(r.get('customer','')).lower() or k in str(r.get('project_code','')).lower() or k in str(r.get('po_number','')).lower()]
    for r in rows:r['advance_required'],r['balance_required'],r['total_received'],r['outstanding'],r['clearance']=clearance(r)
    return rows

def documents(order_id): return client().table('documents').select('*').eq('order_id',order_id).order('uploaded_at',desc=True).execute().data

def show_order(r):
    a,b,total,out,status=clearance(r)
    st.subheader(f"{r['project_code']} · {r['customer']}")
    c1,c2,c3,c4=st.columns(4);c1.metric('PO',r['po_number']);c2.metric('Quantity',r['quantity']);c3.metric('Received',f"{r['currency']} {total:,.2f}");c4.metric('Outstanding',f"{r['currency']} {out:,.2f}")
    (st.success if status=='CLEARED FOR DELIVERY' else st.warning if status=='WAITING FOR 50% BALANCE' else st.error)(status)
    st.write(f"Advance: **{r['currency']} {float(r['advance_received']):,.2f} / {a:,.2f}**")
    st.write(f"Balance: **{r['currency']} {float(r['balance_received']):,.2f} / {b:,.2f}**")
    st.write(f"Delivery: **{r['delivery_status']}**")
    if r.get('remarks'):st.caption(r['remarks'])
    st.markdown('**Documents**')
    docs=documents(r['id'])
    if not docs:st.caption('No documents uploaded.')
    for d in docs:
        try:
            blob=client().storage.from_('order-documents').download(d['storage_path'])
            st.download_button(f"Download {d['document_type']}: {d['original_name']}",blob,d['original_name'],key=f"doc{d['id']}")
        except Exception: st.warning(f"Document unavailable: {d['original_name']}")

try: count=user_count()
except Exception as e:
    st.error('Cloud database is not configured. Add Streamlit secrets and run schema.sql in Supabase.');st.code(str(e));st.stop()

if count==0:
    st.title('First-time secure setup');st.info('Create the first Finance Admin account. There is no default password.')
    with st.form('setup'):
        name=st.text_input('Full name');email=st.text_input('Company email');pw=st.text_input('Password',type='password');confirm=st.text_input('Confirm password',type='password');ok=st.form_submit_button('Create Finance Admin')
    if ok:
        if not name or '@' not in email or len(pw)<10 or pw!=confirm:st.error('Use a valid email and matching password of at least 10 characters.')
        else:create_user(email,name,pw,'FINANCE_ADMIN');st.success('Finance Admin created.');st.rerun()
    st.stop()
if 'user' not in st.session_state:
    st.title('📷 TSI Camera Order & Delivery Control')
    with st.form('login'):
        email=st.text_input('Company email');pw=st.text_input('Password',type='password');ok=st.form_submit_button('Sign in')
    if ok:
        user=authenticate(email,pw)
        if user:st.session_state.user=user;st.rerun()
        st.error('Invalid sign-in or inactive account.')
    st.stop()

user=st.session_state.user
st.sidebar.markdown(f"**{user['full_name']}**");st.sidebar.caption(user['role'].replace('_',' ').title())
if st.sidebar.button('Sign out'):logout()
pages=['Dashboard','Orders','Documents','Users','Audit Log'] if user['role']=='FINANCE_ADMIN' else ['Search & View']
page=st.sidebar.radio('Menu',pages)

if page=='Dashboard':
    require_admin();rows=order_rows();wa=sum(r['clearance']=='WAITING FOR 50% ADVANCE' for r in rows);wb=sum(r['clearance']=='WAITING FOR 50% BALANCE' for r in rows);ready=sum(r['clearance']=='CLEARED FOR DELIVERY' for r in rows)
    st.markdown('''<div class="portal-hero"><div><div class="eyebrow">TSI · FINANCE OPERATIONS</div><div class="title">Camera Order & Delivery Control</div><div class="sub">Payment clearance, order documents and delivery readiness in one controlled portal.</div></div><div class="live"><b></b> LIVE CONTROL</div></div>''',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4);c1.metric('ACTIVE ORDERS',len(rows));c2.metric('ADVANCE DUE',wa);c3.metric('BALANCE DUE',wb);c4.metric('READY',ready)
    st.markdown('### Order Control');search=st.text_input('Search',placeholder='Search customer, project code or PO number',label_visibility='collapsed')
    for r in order_rows(search):
        status=r['clearance'];cls='green' if status=='CLEARED FOR DELIVERY' else 'amber' if status=='WAITING FOR 50% BALANCE' else 'red';label='CLEARED' if cls=='green' else 'BALANCE PENDING' if cls=='amber' else 'ADVANCE PENDING'
        st.markdown(f'''<div class="order"><div class="main"><strong>{r['project_code']}</strong><div>{r['customer']}</div><div class="meta">PO {r['po_number']} · {r['quantity']} camera(s)</div></div><div class="money"><span>CONTRACT VALUE</span><strong>{r['currency']} {float(r['contract_amount']):,.2f}</strong></div><div class="money"><span>OUTSTANDING</span><strong>{r['currency']} {float(r['outstanding']):,.2f}</strong></div><div><span class="badge {cls}">{label}</span></div></div>''',unsafe_allow_html=True)
elif page=='Orders':
    require_admin();st.title('Orders and Payments');t1,t2=st.tabs(['Add order','Update order/payment'])
    with t1:
        with st.form('add'):
            project=st.text_input('Project code');customer=st.text_input('Customer');po=st.text_input('PO number');qty=st.number_input('Quantity',min_value=0,step=1);amount=st.number_input('Contract amount',min_value=0.0);currency=st.selectbox('Currency',['AED','USD','SGD']);remarks=st.text_area('Remarks');ok=st.form_submit_button('Create order')
        if ok:
            row={'project_code':project,'customer':customer,'po_number':po,'quantity':qty,'contract_amount':amount,'currency':currency,'remarks':remarks,'created_by':user['id'],'updated_by':user['id']}
            created=client().table('orders').insert(row).execute().data[0];audit(user['id'],'ORDER_CREATED',po,created['id']);st.success('Order created.');st.rerun()
    with t2:
        rows=order_rows();opts={f"{r['project_code']} | {r['po_number']} | {r['customer']}":r for r in rows}
        if opts:
            r=opts[st.selectbox('Order',opts)]
            with st.form('update'):
                adv=st.number_input('Advance received',min_value=0.0,value=float(r['advance_received']));bal=st.number_input('Balance received',min_value=0.0,value=float(r['balance_received']));delivery=st.selectbox('Delivery status',['NOT DELIVERED','READY FOR DELIVERY','DELIVERED','CANCELLED'],index=['NOT DELIVERED','READY FOR DELIVERY','DELIVERED','CANCELLED'].index(r['delivery_status']));remarks=st.text_area('Remarks',r.get('remarks') or '');ok=st.form_submit_button('Save update')
            if ok:
                client().table('orders').update({'advance_received':adv,'balance_received':bal,'delivery_status':delivery,'remarks':remarks,'updated_by':user['id']}).eq('id',r['id']).execute();audit(user['id'],'ORDER_UPDATED',f'advance={adv}, balance={bal}, delivery={delivery}',r['id']);st.success('Updated.');st.rerun()
elif page=='Documents':
    require_admin();st.title('Documents');rows=order_rows();opts={f"{r['project_code']} | {r['po_number']}":r for r in rows}
    if opts:
        r=opts[st.selectbox('Order',opts)];dtype=st.selectbox('Document type',['PO','ADVANCE_INVOICE','BALANCE_INVOICE','TAX_INVOICE','OTHER']);file=st.file_uploader('PDF only',type=['pdf'])
        if st.button('Upload',disabled=file is None):
            path=f"{r['id']}/{uuid4().hex}.pdf";client().storage.from_('order-documents').upload(path,file.getvalue(),{'content-type':'application/pdf'});doc={'order_id':r['id'],'document_type':dtype,'original_name':file.name,'storage_path':path,'uploaded_by':user['id']};client().table('documents').insert(doc).execute();audit(user['id'],'DOCUMENT_UPLOADED',f'{dtype}: {file.name}',r['id']);st.success('Uploaded.');st.rerun()
        show_order(r)
elif page=='Users':
    require_admin();st.title('User Access')
    with st.form('user'):
        name=st.text_input('Full name');email=st.text_input('Company email');pw=st.text_input('Temporary password',type='password');role=st.selectbox('Role',['TEAM_VIEWER','FINANCE_ADMIN']);ok=st.form_submit_button('Create user')
    if ok:
        if len(pw)<10:st.error('Password must be at least 10 characters.')
        else:create_user(email,name,pw,role,user['id']);st.success('User created.');st.rerun()
    st.dataframe(pd.DataFrame(client().table('portal_users').select('id,email,full_name,role,active,created_at').order('full_name').execute().data),use_container_width=True,hide_index=True)
elif page=='Audit Log':
    require_admin();st.title('Audit Log');st.dataframe(pd.DataFrame(client().table('audit_log').select('*').order('created_at',desc=True).limit(500).execute().data),use_container_width=True,hide_index=True)
else:
    st.title('Camera Order & Delivery Portal');st.caption('View-only access. Search status and download approved documents.');q=st.text_input('Search customer, project code, or PO number')
    if q:
        rows=order_rows(q)
        if not rows:st.warning('No matching order found.')
        for r in rows:
            with st.container(border=True):show_order(r)
    else:st.info('Enter a customer, project code, or PO number.')
