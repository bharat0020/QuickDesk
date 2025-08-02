
# QuickDesk - Help Desk Ticketing System

QuickDesk is a simple and efficient help desk solution designed to streamline support communication. It allows users to raise support tickets while enabling support agents and administrators to manage and resolve issues effectively.

---

## 🔍 Project Overview

QuickDesk provides a user-friendly interface for different user roles:

- **End Users** (Employees or Customers): Can create and track their support tickets.
- **Support Agents**: Can view, update, and resolve tickets.
- **Admins**: Can manage users, monitor ticket statuses, and assign tickets to agents.

---

## ✨ Features

### 🔸 End Users
- Submit new support tickets
- View status and responses of submitted tickets
- Get email notifications on status updates (if configured)

### 🔸 Support Agents
- View assigned tickets
- Update ticket status and provide responses
- Add internal notes and close tickets

### 🔸 Admins
- View all tickets in the system
- Manage users (Agents, Customers)
- Assign tickets to agents
- Dashboard overview

---

## 🧰 Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Node.js (Express)
- **Database**: MongoDB (optional, depending on your implementation)
- **Authentication**: (Optional) JWT / Sessions
- **Deployment**: GitHub Pages / Heroku / Render / Vercel

---

## 🛠️ Setup Instructions

1. **Clone the Repository**

```bash
git clone https://github.com/your-username/quickdesk.git
cd quickdesk
```

2. **Install Dependencies**  
   (Only if backend is included in your version)

```bash
npm install
```

3. **Start the App**

```bash
# For development
npm run dev
# or
node server.js
```

4. **Open in Browser**  
   Visit `http://localhost:5000`

---

## 📂 Folder Structure

```bash
QuickDesk/
├── QuickDesk/ 
   |── instance
      |── quickdesk.db     #automatically created when run               
   ├── static/
      ├── css/
      |  ├── style.css
      |── js
      |  ├── main.js
   |── templates/
      |── admin/
         |── categories.html
         |── users.html
      |── auth/
         |── login.html
         |── register.html
      |── errors/
         |── 403.html
         |── 404.html
         |── 500.html
      |── tickets/
         |── create.html
         |── list.html
         |── view.html
      |── base.html
      |── dashboard.html
      |── index.html  
   |── uploads  
      |── .gitkeep   
   |── app.py
   |── form.py
   |── main.py
   |── models.py
   |── routes.py
   |── setup_roles.py
   |── utils.py

---

## 🧪 Usage Guide

- Navigate to the homepage
- Register or log in (if authentication is present)
- Submit a ticket or manage tickets based on your role
- Admins can manage users and oversee ticket flow

---

## 🙋‍♂️ Contributing

Contributions are welcome!  
1. Fork this repo  
2. Create a new branch  
3. Submit a pull request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 📬 Contact

For queries or support:
- **Team Name**: CodeDrop
- **Author**: Bharat Mittal, Abhitesh, Lalatendu Biswal, Ayushi 
- **Email**: [bmittal189@gmail.com] [avi.vish02244@gmail.com] [lalatendu118@gmail.com] [ayu.rana001@gmail.com]


---

