# Flask Server with PostgreSQL and SMS Gateway

This project provides a Flask server for managing user authentication, including OTP verification, integrated with a PostgreSQL database. It also connects to an SMS Gateway for sending and receiving SMS.

---

## **Features**

- User registration and OTP generation
- OTP verification and JWT token-based authentication
- PostgreSQL as the database
- Dockerized for easy deployment
- Integration with a Python 2.7 SMS Gateway

---

## **Prerequisites**

- Docker (v20.10+)
- Docker Compose (v1.29+)

---

## **Setup Instructions**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd flask-server
```

---

### 2. Environment Configuration

Create a `.env` file in the root directory and add the required environment variables:

```plaintext
# Flask Server Environment
DATABASE_URL=postgresql://user:password@db:5432/dbname
JWT_SECRET_KEY=your_jwt_secret_key
SMS_GATEWAY_URL=http://sms-gateway:5000/send-sms

# PostgreSQL Environment
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=dbname
```

---

### 3. Build and Start the Containers

1. **Build the Docker images**:
   ```bash
   docker-compose build
   ```

2. **Start the containers**:
   ```bash
   docker-compose up -d
   ```

3. **Check running containers**:
   ```bash
   docker ps
   ```

---

### 4. Initialize the Database

Run the following command to create the required tables in PostgreSQL:

```bash
docker-compose exec flask-server python init_db.py
```

---

## **Endpoints**

### **1. User Registration**
**URL**: `/auth/register`  
**Method**: `POST`  
**Description**: Registers a user and sends an OTP via SMS.

**Request Body**:
```json
{
  "phone_number": "+1234567890",
  "name": "John Doe"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "OTP sent successfully"
}
```

---

### **2. Verify OTP**
**URL**: `/auth/verify-otp`  
**Method**: `POST`  
**Description**: Verifies the OTP and generates a JWT token.

**Request Body**:
```json
{
  "phone_number": "+1234567890",
  "otp": "123456"
}
```

**Response**:
```json
{
  "status": "success",
  "access_token": "your_jwt_token"
}
```

---

### **3. Send SMS (via SMS Gateway)**
**URL**: `/send-sms`  
**Method**: `POST`  
**Description**: Sends an SMS to a specified phone number.

**Request Body**:
```json
{
  "phone_number": "+1234567890",
  "message": "Hello, this is a test message."
}
```

---

## **Testing the Application**

1. **Test Registration**:
   ```bash
   curl -X POST http://localhost:5000/auth/register \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890", "name": "John Doe"}'
   ```

2. **Test OTP Verification**:
   ```bash
   curl -X POST http://localhost:5000/auth/verify-otp \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890", "otp": "123456"}'
   ```

3. **Test SMS Sending**:
   ```bash
   curl -X POST http://localhost:5001/send-sms \
        -H "Content-Type: application/json" \
        -d '{"phone_number": "+1234567890", "message": "Hello!"}'
   ```

---

## **Stopping the Containers**

To stop the containers, run:
```bash
docker-compose down
```

---

## **Logs and Debugging**

1. View Flask server logs:
   ```bash
   docker logs flask-server
   ```

2. View PostgreSQL logs:
   ```bash
   docker logs postgres-db
   ```

3. View SMS Gateway logs:
   ```bash
   docker logs sms-gateway
   ```

---

## **Future Enhancements**

- Add role-based access control for users.
- Implement additional endpoints for user management.
- Add email verification along with OTP.

---

## **Contributing**

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Submit a pull request.

---

## **License**

This project is licensed under the MIT License. See the LICENSE file for details.
