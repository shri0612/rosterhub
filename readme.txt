RosterHub Application – Setup Instructions

1. Clone the project from GitHub:
   git clone <your-repo-link>

2. Navigate to the project folder:
   cd rosterhub

3. Create and activate virtual environment:
   python3 -m venv venv
   source venv/bin/activate

4. Install required dependencies:
   pip install -r requirements.txt

5. Set environment variables:
   Create a .env file and add required keys such as:

* Email credentials
* API URLs

6. Apply database migrations:
   python manage.py migrate

7. Collect static files:
   python manage.py collectstatic

8. Run the application:
   python manage.py runserver

9. Open in browser:
   http://127.0.0.1:8000/

Note:

* Make sure AWS services and external APIs are running.
* For CI/CD deployment, GitHub Actions is used to deploy to EC2.

