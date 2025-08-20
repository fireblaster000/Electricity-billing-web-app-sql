# Electricity Distribution Company Billing System

A comprehensive web-based billing management system for electricity distribution companies, built with FastAPI, Oracle Database, and modern web technologies.

## 🏗️ System Architecture

This application follows a three-tier architecture:

- **Presentation Layer**: HTML templates with CSS styling and JavaScript for user interaction
- **Application Layer**: FastAPI-based web server handling business logic and API endpoints
- **Data Layer**: Oracle Database with stored procedures and functions for data management

## 🚀 Features

### 1. Bill Retrieval & Generation

- **Comprehensive Bill Details**: Customer information, connection details, usage statistics
- **Dynamic Calculations**: Real-time computation of tariffs, taxes, subsidies, and fees
- **Billing History**: Display of previous 10 bills with payment status
- **Multiple Rate Structures**: Support for peak/off-peak pricing and connection-based tariffs

### 2. Payment Processing

- **Multiple Payment Methods**: Support for various payment options (credit card, bank transfer, etc.)
- **Payment Validation**: Prevents overpayment and handles partial payments
- **Real-time Status Updates**: Automatic calculation of outstanding amounts
- **Payment Receipts**: Detailed transaction records with timestamps

### 3. Bill Adjustment Management

- **Administrative Controls**: Officer authorization required for bill modifications
- **Audit Trail**: Complete record of adjustments with reasons and timestamps
- **Validation Rules**: Prevents adjustments on fully paid bills
- **Receipt Generation**: Detailed adjustment documentation

## 📋 System Requirements

### Software Dependencies

- Python 3.8+
- Oracle Database 19c or higher
- Nginx Web Server
- Uvicorn ASGI Server

### Python Libraries

```
fastapi==0.115.4
oracledb==2.4.1
uvicorn==0.32.0
jinja2==3.1.4
python-multipart==0.0.17
```

## 🛠️ Installation & Setup

### 1. Oracle Cloud Infrastructure Setup

1. Create an Oracle Cloud account and set up a VM instance
2. Configure Ubuntu 22.04 as the operating system
3. Set up Virtual Cloud Network (VCN) security rules for HTTP traffic (port 80)
4. Download and securely store your SSH private key

### 2. Database Configuration

1. Set up Oracle Database connection
2. Place your wallet files in the application directory
3. Update `sqlnet.ora` with correct wallet path
4. Configure environment variables in `env.sh`:
   ```bash
   export DB_USERNAME="your_username"
   export DB_PASSWORD="your_password"
   export DB_ALIAS="your_database_alias"
   export ORACLE_HOME="/path/to/oracle/client"
   ```

### 3. Server Deployment

1. Copy project files to your server:

   ```bash
   scp -i <ssh-key> -r /local/project/path user@server-ip:/server/path
   ```

2. Make setup scripts executable:

   ```bash
   chmod +x python_environment_setup.sh oracle_client_setup.sh nginx_configuration.sh
   ```

3. Run setup scripts:

   ```bash
   ./python_environment_setup.sh && ./oracle_client_setup.sh && ./nginx_configuration.sh
   ```

4. Launch the application:
   ```bash
   source env.sh
   source venv/bin/activate
   cd application
   fastapi run electricity_billing_app.py
   ```

## 🔧 Application Structure

```
electricity-billing-system/
├── application/
│   ├── electricity_billing_app.py      # Main FastAPI application
│   ├── requirements.txt                 # Python dependencies
│   ├── static/
│   │   └── billing_styles.css          # Application styling
│   └── templates/
│       ├── index.html               # Main dashboard
│       ├── bill_search.html             # Bill retrieval form
│       ├── bill_details_view.html       # Detailed bill display
│       ├── payment_form.html            # Payment processing form
│       ├── payment_confirmation.html    # Payment receipt
│       ├── adjustment_form.html         # Bill adjustment form
│       └── adjustment_confirmation.html # Adjustment receipt
├── environment_config.sh                # Environment variables
├── nginx_configuration.sh              # Nginx setup
├── oracle_client_setup.sh              # Oracle client installation
└── python_environment_setup.sh         # Python environment setup
```

## 💡 Usage Guide

### Accessing the System

Navigate to `http://your-server-ip` to access the main dashboard.

### Bill Retrieval

1. Click "Bill Retrieval" from the dashboard
2. Enter required information:
   - Customer ID
   - Connection ID
   - Billing Month (1-12)
   - Billing Year
3. View comprehensive bill details including:
   - Customer and connection information
   - Usage statistics and billing amounts
   - Applied tariffs, taxes, and subsidies
   - Payment history

### Processing Payments

1. Select "Bill Payment" from the dashboard
2. Provide payment details:
   - Bill ID
   - Payment amount
   - Payment method ID
3. System validates payment and updates bill status
4. Receive detailed payment confirmation

### Bill Adjustments

1. Access "Bill Adjustment" from the dashboard
2. Enter adjustment information:
   - Bill ID (auto-populates original amount)
   - Officer name and designation
   - Adjustment amount and reason
3. System processes adjustment with full audit trail
4. Generate adjustment receipt for records

## 🔍 Key Features Deep Dive

### Dynamic Billing Calculations

The system performs real-time calculations using Oracle stored procedures:

- **Peak/Off-Peak Usage**: Separate rates for different time periods
- **Tariff Application**: Connection-type specific rate structures
- **Tax Computation**: Automated tax calculations based on usage
- **Subsidy Processing**: Income-based and usage-based subsidies
- **Arrears Management**: Outstanding balance tracking

### Payment Processing Engine

- **Multi-Method Support**: Credit cards, bank transfers, online payments
- **Partial Payment Handling**: Tracks outstanding balances
- **Payment Validation**: Prevents duplicate and invalid payments
- **Status Management**: Automatic updates to payment status

### Administrative Controls

- **Officer Authorization**: Required approvals for bill adjustments
- **Audit Logging**: Complete transaction history
- **Error Handling**: Comprehensive validation and user feedback
- **Security Features**: Input validation and SQL injection prevention

## 🔒 Security Features

- **Input Validation**: All user inputs are validated and sanitized
- **SQL Injection Prevention**: Parameterized queries throughout
- **Access Controls**: Officer-level permissions for sensitive operations
- **Audit Trails**: Complete logging of all transactions and changes

## 🚨 Error Handling

The application includes comprehensive error handling:

- Invalid customer/connection IDs
- Non-existent bills
- Payment validation errors
- Database connection issues
- User-friendly error messages via alerts

## 📊 Database Schema

The system works with a comprehensive database schema including:

- **Customers**: Customer information and contact details
- **Connections**: Service connections and meter information
- **Bills**: Billing records with amounts and dates
- **PaymentDetails**: Payment transactions and methods
- **Tariffs**: Rate structures and pricing information
- **Taxes & Subsidies**: Financial adjustments and calculations

## 🤝 Support & Maintenance

### Monitoring

- Application logs via Uvicorn
- Database connection status monitoring
- Error tracking and reporting

### Backup & Recovery

- Regular database backups recommended
- Application file versioning
- Configuration backup procedures

## 📈 Performance Considerations

- **Database Optimization**: Indexed queries for fast retrieval
- **Connection Pooling**: Efficient database connection management
- **Caching Strategy**: Static file caching via Nginx
- **Scalability**: Three-tier architecture supports horizontal scaling

## 🔄 Future Enhancements

Potential areas for system expansion:

- Mobile application interface
- Automated payment scheduling
- Advanced reporting and analytics
- Integration with smart meters
- Customer self-service portal
- Multi-language support

---

_This electricity billing system provides a robust, scalable solution for utility companies to manage customer billing, payments, and account adjustments efficiently._
