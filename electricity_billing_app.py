from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import datetime
import os
import logging
import oracledb
import uvicorn

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

d = os.environ.get("ORACLE_HOME")               # Defined by the file `oic_setup.sh`
oracledb.init_oracle_client(lib_dir=d)          # Thick mode

# These environment variables come from `env.sh` file.
user_name = os.environ.get("DB_USERNAME")
user_pswd = os.environ.get("DB_PASSWORD")
db_alias  = os.environ.get("DB_ALIAS")

# Database connection
try:
    connection = oracledb.connect(
        user=user_name,
        password=user_pswd,
        dsn=db_alias
    )
    logger.info("Database connection established successfully.")
    print("connection established")
except Exception as e:
    logger.error(f"Error connecting to the database: {e}")
    raise


# make sure to setup connection with the DATABASE SERVER FIRST. refer to python-oracledb documentation for more details on how to connect, and run sql queries and PL/SQL procedures.

app = FastAPI()

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

origins = ['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
) 
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


# -----------------------------
# API Endpoints
# -----------------------------

# ---------- GET methods for the pages ----------
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Bill payment page
@app.get("/bill-payment", response_class=HTMLResponse)
async def get_bill_payment(request: Request):
    return templates.TemplateResponse("bill_payment.html", {"request": request})

# Bill generation page
@app.get("/bill-retrieval", response_class=HTMLResponse)
async def get_bill_retrieval(request: Request):
    return templates.TemplateResponse("bill_retrieval.html", {"request": request})

# Adjustments page
@app.get("/bill-adjustments", response_class=HTMLResponse)
async def get_bill_adjustment(request: Request):
    return templates.TemplateResponse("bill_adjustment.html", {"request": request})


# ---------- POST methods for the pages ----------
@app.post("/bill-payment", response_class=HTMLResponse)
async def post_bill_payment(
    request: Request,
    bill_id: int = Form(...),
    amount: float = Form(...),
    payment_method_id: int = Form(...)
):
    print(f"BillID: {bill_id}, Amount: {amount}, PaymentMethodID: {payment_method_id}")
    
    try:
        # Open a database cursor
        cursor = connection.cursor()

        # Get payment method description
        cursor.execute("""
            SELECT PaymentMethodDescription
            FROM PaymentMethods
            WHERE PaymentMethodID = :payment_method_id
        """, {"payment_method_id": payment_method_id})
        payment_method_desc = cursor.fetchone()
        if not payment_method_desc:
            return JSONResponse({"error": "Invalid Payment Method ID"}, status_code=400)
        
        payment_method_desc = payment_method_desc[0]
        print(f"Payment Method Description: {payment_method_desc}")

        # Retrieve payment status and outstanding amount for the bill
        cursor.execute("""
            SELECT 
                NVL(SUM(pd.AmountPaid), 0) AS TotalPaid, 
                b.TotalAmount_BeforeDueDate, 
                b.TotalAmount_AfterDueDate, 
                b.DueDate,
                MAX(pd.PaymentStatus) AS PaymentStatus
            FROM 
                Bill b
            LEFT JOIN 
                PaymentDetails pd ON b.BillID = pd.BillID
            WHERE 
                b.BillID = :bill_id
            GROUP BY 
                b.TotalAmount_BeforeDueDate, b.TotalAmount_AfterDueDate, b.DueDate
        """, {"bill_id": bill_id})

        bill_info = cursor.fetchone()
        if not bill_info:
            return JSONResponse({"error": "Invalid Bill ID"}, status_code=400)
        
        total_paid = bill_info[0]
        total_amount_before_due = bill_info[1]
        total_amount_after_due = bill_info[2]
        due_date = bill_info[3]
        payment_status = bill_info[4] or "Unpaid"  # Default to "Unpaid" if no record exists
        print(f"Total Paid: {total_paid}, Total Amount Before Due: {total_amount_before_due}, Total Amount After Due: {total_amount_after_due}, Due Date: {due_date}, Payment Status: {payment_status}")

        # Validation: Prevent processing if the bill is already fully paid
        if payment_status == "Fully Paid":
            print("The bill is already fully paid. Payment processing halted.")
            return JSONResponse({"error": "The bill is already fully paid."}, status_code=400)

        # Determine outstanding amount
        payment_date = datetime.datetime.now()
        outstanding_amount = (total_amount_before_due if payment_date <= due_date else total_amount_after_due) - total_paid
        print(f"Outstanding Amount: {outstanding_amount}")

        # Validation: Check if the amount being paid exceeds the outstanding amount
        if outstanding_amount <= 0:
            print("No outstanding amount to pay. Payment processing halted.")
            return JSONResponse({"error": "No outstanding amount to pay."}, status_code=400)

        if amount > outstanding_amount:
            print(f"The payment amount ({amount}) exceeds the outstanding amount ({round(outstanding_amount, 2)}). Payment processing halted.")
            return JSONResponse({"error": f"The payment amount (${amount}) exceeds the outstanding amount (${round(outstanding_amount, 2)})."}, status_code=400)

        # Process the payment using the PL/SQL function
        payment_result = cursor.callfunc(
            "fun_process_Payment",
            int,
            [bill_id, payment_date, payment_method_id, amount]
        )
        
        if payment_result == -1:
            return JSONResponse({"error": "Payment processing failed. Please check your inputs."}, status_code=400)
        
        print(f"Payment processed successfully for Bill ID: {bill_id}, Payment Amount: {amount}")

        # Update outstanding amount and status after payment
        outstanding_amount -= amount
        payment_status = "FULLY PAID" if outstanding_amount <= 0 else "PARTIALLY PAID"
        print(f"Updated Outstanding Amount: {outstanding_amount}, Updated Payment Status: {payment_status}")

        # Commit the transaction
        connection.commit()  # <-- Ensure changes are saved to the database
        print("Transaction committed successfully.")

        # Prepare payment details dictionary
        payment_details = {
            "bill_id": bill_id,
            "amount": amount,
            "payment_method_id": payment_method_id,
            "payment_method_description": payment_method_desc,
            "payment_date": payment_date.strftime("%Y-%m-%d %H:%M:%S"),
            "payment_status": payment_status,
            "outstanding_amount": round(outstanding_amount, 2),
        }

        return templates.TemplateResponse("payment_receipt.html", {"request": request, "payment_details": payment_details})

    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        connection.rollback()  # <-- Rollback changes if an error occurs
        return JSONResponse({"error": "Failed to process payment"}, status_code=500)





@app.post("/bill-retrieval", response_class=HTMLResponse)
async def post_bill_retrieval(
    request: Request,
    customer_id: str = Form(...),
    connection_id: str = Form(...),
    month: int = Form(...),
    year: int = Form(...)
):
    print(f"customerid: {customer_id}, connectionid: {connection_id}, month: {month}, year: {year}")
    try:
        cursor = connection.cursor()

        # Query to retrieve customer, connection, and bill details
        cursor.execute("""
            SELECT 
                c.CustomerID, c.FirstName, c.LastName, c.CustomerType, c.OrgName, 
                c.Address AS CustomerAddress, c.PhoneNumber AS CustomerPhone, c.Email AS CustomerEmail,
                ct.Description AS ConnectionType, con.DivisionID, con.SubDivID, con.InstallationDate, con.MeterType, 
                b.BillIssueDate, b.Net_PeakUnits, b.Net_OffPeakUnits, b.TotalAmount_BeforeDueDate, 
                b.DueDate, b.TotalAmount_AfterDueDate, b.BillingMonth, b.BillingYear, 
                b.Arrears, b.FixedFee, b.TaxAmount, di.DivisionName, di.SubDivName
            FROM 
                Customers c
            JOIN 
                Connections con ON c.CustomerID = con.CustomerID
            JOIN 
                ConnectionTypes ct ON con.ConnectionTypeCode = ct.ConnectionTypeCode
            JOIN 
                Bill b ON con.ConnectionID = b.ConnectionID
            JOIN 
                DivInfo di ON con.DivisionID = di.DivisionID AND con.SubDivID = di.SubDivID
            WHERE 
                c.CustomerID = :customer_id 
                AND con.ConnectionID = :connection_id 
                AND b.BillingMonth = :month 
                AND b.BillingYear = :year
        """, {
            "customer_id": customer_id,
            "connection_id": connection_id,
            "month": month,
            "year": year
        })

        bill = cursor.fetchone()

        if not bill:
            return JSONResponse({"error": "No bill found for the given inputs"}, status_code=404)

        cursor.execute("""
            SELECT 
                b.BillingMonth, 
                b.BillingYear, 
                b.TotalAmount_BeforeDueDate, 
                b.DueDate, 
                b.TotalAmount_AfterDueDate, 
                pd.PaymentStatus
            FROM 
                Bill b
            LEFT OUTER JOIN 
                PaymentDetails pd ON b.BillID = pd.BillID
            WHERE 
                b.ConnectionID = :connection_id
                AND (
                    (b.BillingYear = :year AND b.BillingMonth < :month) 
                    OR (b.BillingYear < :year)                         
                )
            ORDER BY 
                b.BillingYear DESC, b.BillingMonth DESC 
            FETCH FIRST 10 ROWS ONLY
        """, {"connection_id": connection_id, "month": month, "year": year})
        previous_bills = cursor.fetchall()

        

        # Call necessary functions to compute values dynamically
        billing_days = cursor.callfunc("fun_compute_BillingDays", int, [connection_id, month, year])
        print(f"billing days: {billing_days}")
        import_peak_units = cursor.callfunc("fun_compute_ImportPeakUnits", int, [connection_id, month, year])
        import_off_peak_units = cursor.callfunc("fun_compute_ImportOffPeakUnits", int, [connection_id, month, year])
        export_off_peak_units = cursor.callfunc("fun_compute_ExportOffPeakUnits", int, [connection_id, month, year])
        peak_amount = cursor.callfunc("fun_compute_PeakAmount", float, [connection_id, month, year, bill[13]])
        print(f"peak amount: {peak_amount}")
        off_peak_amount = cursor.callfunc("fun_compute_OffPeakAmount", float, [connection_id, month, year, bill[13]])
        print(f"off peak amount: {off_peak_amount}")
        tax_amount = cursor.callfunc("fun_compute_TaxAmount", float, [connection_id, month, year, bill[13], peak_amount, off_peak_amount])
        fixed_fee = cursor.callfunc("fun_compute_FixedFee", float, [connection_id, month, year, bill[13]])
        subsidy_amount = cursor.callfunc("fun_compute_SubsidyAmount", float, [connection_id, month, year, bill[13], import_peak_units, import_off_peak_units])
        print(f"subsidy amount: {subsidy_amount}")
        arrears = cursor.callfunc("fun_compute_Arrears", float, [connection_id, month, year, bill[13]])

        # Fetch subsidies dynamically with unit-per-hour validation
        cursor.execute("""
            SELECT 
                s.SubsidyDescription AS SubsidyName, 
                sp.ProviderName, 
                s.RatePerUnit, 
                s.ThresholdLow_perHour, 
                s.ThresholdHigh_perHour
            FROM 
                Subsidy s
            JOIN 
                SubsidyProvider sp ON s.ProviderID = sp.ProviderID
            JOIN 
                Connections con ON con.ConnectionTypeCode = s.ConnectionTypeCode
            WHERE 
                con.ConnectionID = :connection_id
                AND :bill_issue_date BETWEEN s.StartDate AND s.EndDate
        """, {"connection_id": connection_id, "bill_issue_date": bill[13]})

        subsidies = cursor.fetchall()

        # Compute unit-per-hour subsidy dynamically
        unit_per_hour_subsidy = (import_peak_units + import_off_peak_units) / (billing_days * 24)
        print(f"Unit Per Hour Subsidy: {unit_per_hour_subsidy}")

        subsidy_details = []

        # Validate and calculate subsidies
        for row in subsidies:
            subsidy_name = row[0]  # SubsidyDescription
            provider_name = row[1]  # ProviderName
            rate_per_unit = row[2]  # RatePerUnit
            threshold_low = row[3]  # ThresholdLow_perHour
            threshold_high = row[4]  # ThresholdHigh_perHour

            # Check if the unit-per-hour subsidy falls within the valid range
            if threshold_low <= unit_per_hour_subsidy < threshold_high:
                subsidy_amount = unit_per_hour_subsidy * (24 * billing_days) * rate_per_unit
                subsidy_details.append({
                    "name": subsidy_name,
                    "provider_name": provider_name,
                    "rate_per_unit": rate_per_unit,
                    "threshold_low": threshold_low,
                    "threshold_high": threshold_high,
                    "amount": round(subsidy_amount, 2)
                })

        # If no subsidies found, include a message
        if not subsidy_details:
            subsidy_details.append({
                "name": "No Subsidy Found",
                "provider_name": "N/A",
                "rate_per_unit": "N/A",
                "threshold_low": "N/A",
                "threshold_high": "N/A",
                "amount": 0.0
            })

        print(f"Subsidy Details: {subsidy_details}")


        # Query applicable tariffs for the connection
        cursor.execute("""
            SELECT 
                TariffCode, RatePerUnit, MinAmount, MinUnit, ThresholdLow_perHour, 
                ThresholdHigh_perHour, TarrifDescription, TariffType
            FROM 
                Tariff
            WHERE 
                ConnectionTypeCode = (SELECT ConnectionTypeCode FROM Connections WHERE ConnectionID = :connection_id)
                AND StartDate <= :bill_issue_date AND EndDate >= :bill_issue_date
        """, {"connection_id": connection_id, "bill_issue_date": bill[13]})

        tariffs = cursor.fetchall()

        # Calculate Average Hourly Consumption for Peak and Off-Peak
        ahpc = import_peak_units / (billing_days * 24)  # Average Hourly Peak Consumption
        ahoc = (import_off_peak_units - export_off_peak_units) / (billing_days * 24)  # Average Hourly Off-Peak Consumption
        print(f"AHPC: {ahpc}, AHOC: {ahoc}")

        # Process each tariff and determine applicability
        tariff_details = []
        for tariff in tariffs:
            (tariff_code, rate_per_unit, min_amount, min_unit, threshold_low, 
            threshold_high, tariff_desc, tariff_type) = tariff

            # Calculate normalized min units and min amount
            normalized_min_units = (min_unit * billing_days) / 30
            normalized_min_amount = (min_amount * billing_days) / 30

            # Determine applicable consumption and average hourly consumption
            if tariff_type == 1:  # Peak Hour Tariff
                total_usage = import_peak_units
                average_hourly_consumption = ahpc
            elif tariff_type == 2:  # Off-Peak Hour Tariff
                total_usage = import_off_peak_units - export_off_peak_units
                average_hourly_consumption = ahoc
            else:
                continue  # Skip invalid tariff type

            # Check if average hourly consumption is within the threshold range
            if threshold_low <= average_hourly_consumption < threshold_high:
                # Calculate amount
                if total_usage > normalized_min_units:
                    additional_units = total_usage - normalized_min_units
                    amount = (additional_units * rate_per_unit) + normalized_min_amount
                else:
                    amount = normalized_min_amount

                # Append tariff details
                tariff_details.append({
                    "name": tariff_desc,
                    "units": total_usage,
                    "rate": rate_per_unit,
                    "amount": round(amount, 2),
                    "normalized_min_units": round(normalized_min_units, 2),
                    "threshold_low": threshold_low,
                    "threshold_high": threshold_high
                })

        # If no tariffs are applicable, append a default message
        if not tariff_details:
            tariff_details.append({
                "name": "No Tariff Found",
                "units": 0,
                "rate": 0.0,
                "amount": 0.0,
                "normalized_min_units": "N/A",
                "threshold_low": "N/A",
                "threshold_high": "N/A"
            })

        print(f"Tariff Details: {tariff_details}")


        # Fetch taxes dynamically from the database
        cursor.execute("""
            SELECT 
                tr.TaxType AS TaxName,
                tr.Rate AS TaxRate,
                ((:import_peak_units + :import_off_peak_units) * tr.Rate) AS TaxAmount
            FROM 
                TaxRates tr
            JOIN 
                Connections con ON con.ConnectionTypeCode = tr.ConnectionTypeCode
            JOIN 
                Bill b ON b.ConnectionID = con.ConnectionID
            WHERE 
                b.ConnectionID = :connection_id
                AND b.BillingMonth = :month
                AND b.BillingYear = :year
                AND tr.StartDate <= b.BillIssueDate
                AND tr.EndDate >= b.BillIssueDate
        """, {"connection_id": connection_id, "month": month, "year": year, "import_peak_units": peak_amount, "import_off_peak_units": off_peak_amount})

        taxes = cursor.fetchall()

        tax_details = [
            {
                "name": row[0],  # TaxName
                "rate": row[1],  # TaxRate
                "amount": row[2]  # TaxAmount
            }
            # for row in taxes
            for row in taxes[:2]
        ]

        print(f"taxes: {taxes}")

        # Query fixed fees dynamically from the database
        cursor.execute("""
            SELECT 
                FixedChargeType, 
                FixedFee 
            FROM 
                FixedCharges 
            WHERE 
                ConnectionTypeCode = (SELECT ConnectionTypeCode FROM Connections WHERE ConnectionID = :connection_id)
                AND :bill_issue_date BETWEEN StartDate AND EndDate
        """, {"connection_id": connection_id, "bill_issue_date": bill[13]})

        fixed_fees = cursor.fetchall()

        # Create a list of fixed fee details
        fixed_fee_details = [
            {
                "name": row[0],  # ChargeDescription
                "amount": row[1]  # FixedFee
            }
            for row in fixed_fees
        ]


        # Prepare the bill details dictionary
        bill_details = {
            "customer_id": bill[0],
            "connection_id": bill[3],
            "customer_name": f"{bill[1]} {bill[2]}",
            "customer_address": bill[5],
            "customer_phone": bill[6],
            "customer_email": bill[7],
            "connection_type": bill[8],
            "division": bill[24],
            "subdivision": bill[25],
            "installation_date": bill[11].strftime("%Y-%m-%d"),
            "meter_type": bill[12],
            "issue_date": bill[13].strftime("%Y-%m-%d"),
            "net_peak_units": bill[14],
            "net_off_peak_units": bill[15],
            "bill_amount": bill[16],
            "due_date": bill[17].strftime("%Y-%m-%d"),
            "amount_after_due_date": bill[18],
            "month": bill[19],
            "year": bill[20],
            "arrears_amount": arrears,
            "fixed_fee_amount": fixed_fee,
            "tax_amount": tax_amount,
            "tariffs": tariff_details,
            "taxes": tax_details,
            "subsidies": subsidy_details,
            "fixed_fee": fixed_fee_details,
            "bills_prev": [
                {"month": f"{row[1]}-{row[0]:02}", "year": row[1], "amount": row[2], "due_date": row[3].strftime("%Y-%m-%d"), "status": row[5]}
                for row in previous_bills
            ]
        }

        return templates.TemplateResponse("bill_details.html", {"request": request, "bill_details": bill_details})

    except Exception as e:
        logger.error(f"Error retrieving bill details: {e}")
        return JSONResponse({"error": "Failed to retrieve bill details"}, status_code=500)

@app.post("/bill-adjustments", response_class=HTMLResponse)
async def post_bill_adjustments(
    request: Request,
    bill_id: int = Form(...),
    officer_name: str = Form(...),
    officer_designation: str = Form(...),
    original_bill_amount: float = Form(...),
    adjustment_amount: float = Form(...),
    adjustment_reason: str = Form(...)
):
    try:
        print(f"og bill amount: {original_bill_amount}")
        # Open a database cursor
        cursor = connection.cursor()

        # Retrieve bill details including payment status and outstanding amount
        cursor.execute("""
            SELECT 
                NVL(SUM(pd.AmountPaid), 0) AS TotalPaid,
                b.TotalAmount_BeforeDueDate,
                b.TotalAmount_AfterDueDate,
                b.DueDate,
                MAX(pd.PaymentStatus) AS PaymentStatus
            FROM 
                Bill b
            LEFT JOIN 
                PaymentDetails pd ON b.BillID = pd.BillID
            WHERE 
                b.BillID = :bill_id
            GROUP BY 
                b.TotalAmount_BeforeDueDate, b.TotalAmount_AfterDueDate, b.DueDate
        """, {"bill_id": bill_id})

        bill_info = cursor.fetchone()
        if not bill_info:
            return JSONResponse({"error": "Invalid Bill ID"}, status_code=400)

        total_paid = bill_info[0]
        total_amount_before_due = bill_info[1]
        total_amount_after_due = bill_info[2]
        due_date = bill_info[3]
        payment_status = bill_info[4] or "Unpaid"  # Default to "Unpaid" if no payment record exists

        # Determine outstanding amount
        adjustment_date = datetime.datetime.now()
        outstanding_amount = (total_amount_before_due if adjustment_date <= due_date else total_amount_after_due) - total_paid

        print(f"Total Paid: {total_paid}, Outstanding Amount: {outstanding_amount}, Payment Status: {payment_status}")

        # Validation: If the bill is fully paid, prevent adjustment
        if payment_status == "Fully Paid" or outstanding_amount <= 0:
            print("Bill is already fully paid. Adjustment not allowed.")
            return JSONResponse({"error": "The bill is already fully paid. Adjustment not allowed."}, status_code=400)

        # Validation: If adjustment amount exceeds outstanding amount, prevent adjustment
        if adjustment_amount > original_bill_amount:
            print(f"Adjustment amount ({adjustment_amount}) exceeds outstanding amount ({outstanding_amount}). Adjustment not allowed.")
            return JSONResponse({"error": f"Adjustment amount (${adjustment_amount}) exceeds outstanding amount (${round(outstanding_amount, 2)}). Adjustment not allowed."}, status_code=400)

        # Generate a unique AdjustmentID
        adjustment_id = cursor.execute("SELECT TRUNC(DBMS_RANDOM.VALUE(100000, 999999)) FROM DUAL").fetchone()[0]
        print(f"Generated Adjustment ID: {adjustment_id}")

        # Call the PL/SQL function to process the adjustment
        result = cursor.callfunc(
            "fun_adjust_Bill",
            int,
            [
                adjustment_id,
                bill_id,
                adjustment_date,
                officer_name,
                officer_designation,
                original_bill_amount,
                adjustment_amount,
                adjustment_reason,
            ],
        )

        # Check the result of the adjustment function
        if result == -1:
            return JSONResponse({"error": "Adjustment failed. Please check your inputs."}, status_code=400)

        # Commit the changes to the database
        connection.commit()
        print("Transaction committed successfully.")

        # Prepare adjustment details for the receipt
        adjustment_details = {
            "adjustment_id": adjustment_id,
            "bill_id": bill_id,
            "officer_name": officer_name,
            "officer_designation": officer_designation,
            "original_bill_amount": round(original_bill_amount, 2),
            "adjustment_amount": round(adjustment_amount, 2),
            "adjustment_reason": adjustment_reason,
            "adjustment_date": adjustment_date.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Render the adjustment receipt page directly and send it in the response
        print(f"request: {request}")
        return templates.TemplateResponse("adjustment_receipt.html", {"request": request, "adjustment_details": adjustment_details})

    except Exception as e:
        logger.error(f"Error processing bill adjustment: {e}")
        connection.rollback()  # Rollback changes in case of an error
        return JSONResponse({"error": "Failed to process bill adjustment"}, status_code=500)


@app.get("/get-original-bill-amount/{bill_id}", response_class=JSONResponse)
async def get_original_bill_amount(bill_id: int):
    try:
        # Open a database cursor
        cursor = connection.cursor()

        # Query to fetch the original bill amount
        cursor.execute("""
            SELECT TotalAmount_BeforeDueDate 
            FROM Bill
            WHERE BillID = :bill_id
        """, {"bill_id": bill_id})

        bill_amount = cursor.fetchone()
        if not bill_amount:
            return JSONResponse({"error": "Invalid Bill ID"}, status_code=404)

        return JSONResponse({"original_bill_amount": round(bill_amount[0], 2)})
    
    except Exception as e:
        logger.error(f"Error fetching original bill amount: {e}")
        return JSONResponse({"error": "Failed to fetch original bill amount"}, status_code=500)



if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=8000)