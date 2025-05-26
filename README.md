# Gatekeepr Backend

This is the backend repository for **Gatekeepr**, built with **Django**.

## 🚀 Getting Started

> **Note:** This project is currently configured for deployment. It will **not run locally out-of-the-box** without adjusting the settings (e.g. environment variables, database configuration, allowed hosts, etc.).

To get the project set up locally (after updating settings accordingly):

### Clone the repository
```bash
git clone https://github.com/fxdnz/gatekeepr-backend.git
``` 
### Navigate into the project directory
```
cd backend-gatekeepr
```
#### Create a virtual environment
```
python -m venv venv
```
# Activate the virtual environment
### On macOS/Linux:
```
source venv/bin/activate
```
### On Windows:
```
venv\Scripts\activate
```
### Install dependencies
```
pip install -r requirements.txt
```
### Run migrations
```
python manage.py migrate
```
### Start the development server
```
python manage.py runserver
```
