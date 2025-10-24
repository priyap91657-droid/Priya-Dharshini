from flask import Flask, render_template_string, request, jsonify, session
import datetime

app = Flask(__name__)
app.secret_key = 'supersecret123'  # session secret key

# Store complaints (in memory)
complaints = {}
complaint_counter = 1000

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# HTML Template with colorful theme, emoji, and button disable for resolved
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Smart Complaint Portal</title>
<style>
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: #333;
    }
    .container {
        max-width: 900px;
        margin: 40px auto;
        background: #f7f9fc;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    h1 { text-align: center; color: #333; }
    .tab-btn {
        margin: 5px;
        padding: 10px 25px;
        border: none;
        cursor: pointer;
        border-radius: 12px;
        font-weight: bold;
        background: #eee;
        color: #333;
        transition: 0.3s;
    }
    .tab-btn:hover { background: #667eea; color: white; }
    .tab-btn.active { background: #667eea; color: white; }
    .tab-content { display: none; margin-top: 20px; }
    .tab-content.active { display: block; }
    .form-group { margin-bottom: 15px; }
    input, textarea, select {
        width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ccc;
        box-sizing: border-box; transition: 0.3s;
    }
    input:focus, textarea:focus, select:focus {
        border-color: #667eea;
        box-shadow: 0 0 5px rgba(102,126,234,0.5);
        outline: none;
    }
    .btn {
        background: #667eea; color: white; border: none;
        padding: 12px 25px; border-radius: 8px; cursor: pointer; transition: 0.3s;
    }
    .btn:hover { background: #5a67d8; }
    .btn:disabled { background: #999; cursor: not-allowed; }
    .alert { padding: 12px; border-radius: 8px; margin-bottom: 15px; }
    .alert-success { background: #d4edda; color: #155724; }
    .alert-danger { background: #f8d7da; color: #721c24; }
    .complaint-item {
        background: #e3e8f0; padding: 12px; border-radius: 10px; margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
</head>
<body>
<div class="container">
<h1>🛡️ Smart Complaint Portal</h1>
<div style="text-align:center;">
    <button class="tab-btn active" onclick="showTab('submit', event)">Submit Complaint</button>
    <button class="tab-btn" onclick="showTab('track', event)">Track Status</button>
    <button class="tab-btn" onclick="showTab('admin', event)">Admin Login</button>
</div>

<!-- Submit Complaint Tab -->
<div id="submit-tab" class="tab-content active">
    <h2>Submit a Complaint</h2>
    <div id="alert-message"></div>
    <form id="complaint-form">
        <div class="form-group"><label>Name *</label><input type="text" name="name" required></div>
        <div class="form-group"><label>Email *</label><input type="email" name="email" required></div>
        <div class="form-group"><label>Phone *</label><input type="tel" name="phone" required></div>
        <div class="form-group">
            <label>Category *</label>
            <select name="category" required>
                <option value="service">Service Issue</option>
                <option value="repair">Hostel Repair</option>
                <option value="food">Mess Food</option>
                <option value="other">Other</option>
            </select>
        </div>
        <div class="form-group">
            <label>Priority *</label>
            <select name="priority" required>
                <option value="low">Low 🙂</option>
                <option value="medium" selected>Medium 😐</option>
                <option value="high">High 😤</option>
                <option value="urgent">Urgent 😡</option>
            </select>
        </div>
        <div class="form-group"><label>Subject *</label><input type="text" name="subject" required></div>
        <div class="form-group"><label>Description *</label><textarea name="description" required></textarea></div>
        <button type="submit" class="btn">Submit Complaint</button>
    </form>
</div>

<!-- Track Tab -->
<div id="track-tab" class="tab-content">
    <h2>Track Complaint</h2>
    <input type="text" id="track-id" placeholder="Enter Complaint ID (e.g. COMP-1001)">
    <button class="btn" onclick="trackComplaint()">Track</button>
    <div id="track-result"></div>
</div>

<!-- Admin Tab -->
<div id="admin-tab" class="tab-content">
    <h2>Admin Login</h2>
    <input type="text" id="admin-username" placeholder="Username"><br><br>
    <input type="password" id="admin-password" placeholder="Password"><br><br>
    <button class="btn" onclick="adminLogin()">Login</button>
    <div id="admin-message"></div>
    <div id="admin-dashboard" style="display:none;">
        <h3>Complaints Dashboard</h3>
        <div id="admin-complaints"></div>
    </div>
</div>
</div>

<script>
function showTab(tab, event){
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(tab + '-tab').classList.add('active');
    event.currentTarget.classList.add('active');
}

document.getElementById('complaint-form').addEventListener('submit', async function(e){
    e.preventDefault();
    const data = Object.fromEntries(new FormData(this));
    const res = await fetch('/submit', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    const result = await res.json();
    if(result.success){
        document.getElementById('alert-message').innerHTML = '<div class="alert alert-success">Complaint Submitted! ID: '+result.complaint_id+'</div>';
        this.reset();
    } else {
        document.getElementById('alert-message').innerHTML = '<div class="alert alert-danger">Error submitting complaint.</div>';
    }
});

async function trackComplaint(){
    const id=document.getElementById('track-id').value.trim();
    if(!id){alert('Enter complaint ID');return;}
    const res=await fetch('/track/'+id);
    const data=await res.json();
    if(data.success){
        const c=data.complaint;
        document.getElementById('track-result').innerHTML=
        `<div class='complaint-item'>
            <b>ID:</b> ${c.id}<br>
            <b>Status:</b> ${c.status}<br>
            <b>Priority:</b> ${c.priority}<br>
            <b>Subject:</b> ${c.subject}<br>
            <b>Description:</b> ${c.description}
        </div>`;
    }else{
        document.getElementById('track-result').innerHTML='<div class="alert alert-danger">Complaint not found.</div>';
    }
}

async function adminLogin(){
    const username=document.getElementById('admin-username').value;
    const password=document.getElementById('admin-password').value;
    const res=await fetch('/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username,password})});
    const data=await res.json();
    if(data.success){
        document.getElementById('admin-message').innerHTML='<div class="alert alert-success">Login Successful</div>';
        document.getElementById('admin-dashboard').style.display='block';
        loadComplaints();
    }else{
        document.getElementById('admin-message').innerHTML='<div class="alert alert-danger">Invalid Credentials</div>';
    }
}

async function loadComplaints(){
    const res = await fetch('/admin/complaints');
    const data = await res.json();
    if(data.success){
        const priorityOrder = { 'urgent': 1, 'high': 2, 'medium': 3, 'low': 4 };
        const priorityEmojis = { 'urgent': '😡', 'high': '😤', 'medium': '😐', 'low': '🙂' };

        const sortedComplaints = data.complaints.sort((a,b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
        document.getElementById('admin-complaints').innerHTML = sortedComplaints.map(c => {
            const emoji = priorityEmojis[c.priority] || '';
            const disabled = c.status === 'resolved' ? 'disabled' : '';
            return `
                <div class='complaint-item'>
                    <b>${c.id}</b> | <b>Status:</b> ${c.status.toUpperCase()} | 
                    <b>Priority:</b> ${c.priority} ${emoji}<br>
                    <b>Subject:</b> ${c.subject}<br>
                    <b>Description:</b> ${c.description}<br><br>
                    <button onclick="updateStatus('${c.id}','processing')" class="btn" ${disabled}>Processing</button>
                    <button onclick="updateStatus('${c.id}','resolved')" class="btn" ${disabled}>Resolved</button>
                </div>`;
        }).join('');
    }
}

async function updateStatus(id,status){
    await fetch('/admin/update-status',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({complaint_id:id,status:status})});
    loadComplaints();
}
</script>
</body>
</html>
"""

# Flask routes
@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/submit', methods=['POST'])
def submit_complaint():
    global complaint_counter
    data = request.get_json()
    complaint_counter += 1
    complaint_id = f"COMP-{complaint_counter}"
    complaint = {
        'id': complaint_id,
        'name': data.get('name'),
        'email': data.get('email'),
        'phone': data.get('phone'),
        'category': data.get('category'),
        'priority': data.get('priority'),
        'subject': data.get('subject'),
        'description': data.get('description'),
        'status': 'pending',
        'date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    complaints[complaint_id] = complaint
    return jsonify({'success': True, 'complaint_id': complaint_id})

@app.route('/track/<complaint_id>')
def track_complaint(complaint_id):
    c = complaints.get(complaint_id)
    if c:
        return jsonify({'success': True, 'complaint': c})
    else:
        return jsonify({'success': False})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('username') == ADMIN_USERNAME and data.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/admin/complaints')
def admin_complaints():
    if not session.get('admin'):
        return jsonify({'success': False})
    return jsonify({'success': True, 'complaints': list(complaints.values())})

@app.route('/admin/update-status', methods=['POST'])
def update_status():
    if not session.get('admin'):
        return jsonify({'success': False})
    data = request.get_json()
    cid = data.get('complaint_id')
    status = data.get('status')
    if cid in complaints:
        complaints[cid]['status'] = status
        return jsonify({'success': True})
    return jsonify({'success': False})

if __name__ == '__main__':
    print("✅ Smart Complaint Portal is running at http://127.0.0.1:5000/")
    app.run(debug=True)
