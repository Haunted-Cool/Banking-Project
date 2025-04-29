from flask import Flask
import mysql.connector
import time
import requests
import smtplib
import yfinance as yf
import random
import time
import msvcrt
from decimal import Decimal, InvalidOperation
import json

def custom_getpass(prompt="Password: "):
    print(prompt, end='', flush=True)
    password = ""
    while True:
        char = msvcrt.getch()
        if char == b'\r':
            break
        elif char == b'\x08': 
            if len(password) > 0:
                password = password[:-1]
                print('\b \b', end='', flush=True)
        else:
            password += char.decode('utf-8')
            print('*', end='', flush=True)
    print()
    return password

positive_responses = {'y', 'yes', 'ye', 'why not', 'sure', 'certainly', 'for sure', 'of course', 'obviously'}
negative_responses = {'no', 'n', 'nah', 'na', 'nope', 'not feeling it', 'obviously not', 'hell no'}

API_KEY = 'urapikeyforconvertingcurrency'
BASE_URL = 'baseurlforconvertingcurrency'

server = smtplib.SMTP('smtp.gmail.com', 587)

sender_email = 'urgmailapiemail'
sender_password = 'theapipassword'

with open('minerstuff.json', 'r') as file:
            data = file.read()
            if not data:
                all_results = {}
            else:
                all_results = json.loads(data)

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="ursqlpassword",
        database="ursqldatabase"
    )


def load_accounts():
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts")
        accounts = cursor.fetchall()
        cursor.execute("SELECT * FROM loans")
        loans = cursor.fetchall()
        cursor.execute("SELECT * FROM transactions")
        transactions = cursor.fetchall()
        cursor.close()
        connection.close()

        accounts_dict = {}
        for account in accounts:
            account_name = account['account_name']
            account['transactions'] = [txn for txn in transactions if txn['account_name'] == account_name]
            account['converted_balances'] = []
            account['loan'] = next((loan for loan in loans if loan['account_name'] == account_name), None)
            accounts_dict[account_name] = account

        return accounts_dict
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}


def save_accounts(accounts):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        for account_name, account in accounts.items():
            cursor.execute("DELETE FROM converted_balances WHERE account_name = %s", (account_name,))
            cursor.execute("DELETE FROM loans WHERE account_name = %s", (account_name,))
            cursor.execute("DELETE FROM transactions WHERE account_name = %s", (account_name,))  
            cursor.execute("""
                REPLACE INTO accounts (account_name, password, balance, first_name, middle_name, last_name, dob, address_line1, address_line2, city, state, zip_code, phone_number, email, country_of_residence, account_type, budget, budget_password, send_email, investment_portfolio, retirement_balance)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                account_name,
                account["password"],
                str(account["balance"]),
                account["first_name"],
                account.get("middle_name", ""),
                account["last_name"],
                account["dob"],
                account["address_line1"],
                account.get("address_line2", ""),
                account["city"],
                account["state"],
                account["zip_code"],
                account["phone_number"],
                account["email"],
                account["country_of_residence"],
                account["account_type"],
                str(account.get("budget", 0)),
                account.get("budget_password", None),
                account.get("send_email"),
                str(account.get("investment_portfolio", {})),
                str(account.get("retirement_balance", 0.0))
            ))

            if "converted_balances" in account:
                for converted_balance in account["converted_balances"]:
                    cursor.execute("""
                        INSERT INTO converted_balances (account_name, currency_type, amount)
                        VALUES (%s, %s, %s)
                    """, (
                        account_name,
                        converted_balance.get("Currency type", ""),
                        str(converted_balance.get("Amount", "0"))
                    ))

            if account.get("loan"):
                cursor.execute("""
                    INSERT INTO loans (account_name, amount, interest_rate, total_amount_due, remaining_balance)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    account_name,
                    str(account["loan"]["amount"]),
                    str(account["loan"]["interest_rate"]),
                    str(account["loan"]["total_amount_due"]),
                    str(account["loan"]["remaining_balance"])
                ))

            if "transactions" in account:
                for transaction in account["transactions"]:
                    cursor.execute("""
                        INSERT INTO transactions (account_name, type, amount, fee)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        account_name,
                        transaction["type"],
                        str(transaction["amount"]),
                        str(transaction.get("fee", "0"))
                    ))

        connection.commit()
        cursor.close()
        connection.close()
    except mysql.connector.Error as err:
        print(f"Error: {err}")


def create_acc(accounts):
    first_name = input("First name: ")
    time.sleep(0.43)
    middle_name = input("Middle name (optional): ")
    time.sleep(0.43)
    last_name = input("Last name: ")
    time.sleep(0.43)
    dob = input("Date of birth (YYYY-MM-DD): ")
    time.sleep(0.43)
    address_line1 = input("Address line 1: ")
    time.sleep(0.43)
    address_line2 = input("Address line 2 (Apartment #, Unit #, etc., optional): ")
    time.sleep(0.43)
    city = input("City: ")
    time.sleep(0.43)
    state = input("State: ")
    time.sleep(0.43)
    zip_code = input("ZIP code: ")
    time.sleep(0.43)
    phone_number = input("Phone number (XXX-XXX-XXXX): ")
    time.sleep(0.43)
    email = input("Email address: ")
    time.sleep(0.43)

    re_enter_email = input("Re-enter email address: ")
    while email != re_enter_email:
        print("Emails do not match. Please re-enter the correct email address.")
        time.sleep(0.43)
        re_enter_email = input("Re-enter email address: ")
        time.sleep(0.43)

    country_of_residence = input("Country: ")
    time.sleep(0.43)

    name = input("What would you like the username of the account to be: ")
    time.sleep(0.43)
    while name in accounts:
        name = input("Sorry, that username is already in use, please choose another one: ")
        time.sleep(0.43)
    password = input("What would you like the password to be (needs to have at least 8 characters): ")
    time.sleep(0.43)
    while len(password) < 8:
        print("Your password was not over 8 characters. Please enter a password that is over 8 characters.")
        time.sleep(0.43)
        password = input("What would you like the password to be (needs to have at least 8 characters): ")
        time.sleep(0.43)

    amount = 0
    transactions = []
    converted = []
    retire_amount = 0
    account_type = input("Would you like to make a checking account, saving account, investment account, and retirement account?(checking, saving, investment, or retirement): ").lower()
    time.sleep(0.43)
    while account_type not in ("checking", "saving", "investment", "retirement"):
        print("Invalid option. Enter one of these: checking, saving, investment, or retirement")
        time.sleep(0.43)
        account_type = input("Would you like to make a checking account, saving account, investment account, and retirement account?(checking, saving, investment, or retirement): ").lower()
    if account_type in ('checking', 'saving', 'investment', 'retirement'):
        deposit = input("Would you like to deposit anything?: ")
        time.sleep(0.43)
        if deposit.lower() in positive_responses:
            amount = float(input("Enter the amount to deposit: "))
            time.sleep(0.43)
            transactions.append({"type": "deposit", "amount": amount})
            if account_type == 'retirement':
                retire_amount = amount
    if account_type == 'investment': 
        accounts[name] = {
            "password": password,
            "balance": amount,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "dob": dob,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "phone_number": phone_number,
            "email": email,
            "country_of_residence": country_of_residence,
            "transactions": transactions,
            "account_type": account_type,
            "converted_balances": converted,
            "budget": 0,
            "budget_password": None,
            "send_email": None,
            'investment_portfolio': {}
        }
    else:
        accounts[name] = {
            "password": password,
            "balance": amount,
            "first_name": first_name,
            "middle_name": middle_name,
            "last_name": last_name,
            "dob": dob,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "phone_number": phone_number,
            "email": email,
            "country_of_residence": country_of_residence,
            "transactions": transactions,
            "account_type": account_type,
            "converted_balances": converted,
            "budget": 0,
            "budget_password": None,
            "send_email": False,
            "retirement_balance": retire_amount if account_type == 'retirement' else None
        }

    save_accounts(accounts)
    send_emails = input("Would you like to get email updates for withdrawals, deposits, etc: ").lower()
    time.sleep(0.43)
    if send_emails in positive_responses:
        accounts[name]['send_email'] = True
        save_accounts(accounts)
        message = f"""\
Subject: Account Creation
            
Dear {accounts[name]['first_name']},
            
    Your account has been created successfully.
            
    Hope you have a great day.
            
Regards,
    Manoj :)
        """
        receiver_email = accounts[name]['email']
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message)
            time.sleep(0.79)
            
            print("Your account has been created successfully.")
            time.sleep(0.79)
        except Exception as e:
            time.sleep(0.79)
            print(f"Failed to send email: {e}")
            time.sleep(0.79)
        finally:
            server.quit()
    elif send_emails in negative_responses:
        time.sleep(0.43)
        accounts[name]['send_email'] = None
        save_accounts(accounts)
    else:
        time.sleep(0.43)
        print("Invalid Option")
        time.sleep(2.5)
        time.sleep(2.76)
        return
    print("Account created successfully.")




def view_investments(name, accounts):
    if not isinstance(accounts[name].get('investment_portfolio'), dict):
        accounts[name]['investment_portfolio'] = {}
        time.sleep(0.43)
        print("You do not have any stocks at the moment.")
        return
    
    investments = accounts[name].get('investment_portfolio', {})
    if investments:
        time.sleep(0.43)
        print("Your Investment(s):")
        time.sleep(0.43)
        for ticker_symbol, investment in investments.items():
            print(f"{ticker_symbol}: {investment['shares']} share(s) at ${investment['price']:.2f} per share")
            time.sleep(0.43)
    else:
        print("No investments found.")
        time.sleep(0.43)

def add_investment(name, accounts):
    if accounts[name].get('investment_portfolio') is None or not isinstance(accounts[name]['investment_portfolio'], dict):
        accounts[name]['investment_portfolio'] = {}

    stock_name = input('What stock would you like to buy (Please enter the ticker symbol of the stock): ').upper()
    time.sleep(0.43)
    stock = yf.Ticker(stock_name)
    stock_price = stock.history(period='1d')['Close'].iloc[0]
    time.sleep(0.43)
    check_amount = input(f"Would you like to check how much one share of {stock_name} costs? ").lower()
    time.sleep(0.43)

    if check_amount in positive_responses:
        time.sleep(0.43)
        show_amount = f"One share of {stock_name} costs ${stock_price:.2f} right now."
        time.sleep(0.43)
        print(show_amount)
        keep_going = input("Would you like to still purchase these shares? ").lower()
        time.sleep(0.43)
        if keep_going in positive_responses:
            pass
        elif keep_going in negative_responses:
            print("Alright, have a good day.")
            time.sleep(0.43)
            return
        else:
            print("Invalid option.")
            time.sleep(0.43)
            return
    elif check_amount in negative_responses:
        pass
    else:
        print("Invalid option.")
        time.sleep(0.43)
        return
    
    amount = float(input('Enter the amount of shares you would like to invest: '))
    time.sleep(0.73)
    portfolio = accounts[name].get("investment_portfolio", {})
    
    if stock_name in portfolio:
        wow = input("It seems like you already bought this stock before. Would you like to buy more, view how much you have of the current stock, update how much you would like to buy, or exit (buy more, view, update, exit): ").replace(" ", "").lower()
        time.sleep(0.73)
        if wow == 'buymore':
            what = portfolio[stock_name]["shares"]
            what = float(what) 
            what += amount
            portfolio[stock_name]["shares"] = what
        elif wow == 'view':
            print(f"The stock: {stock_name}, you have invested {portfolio[stock_name]['shares']} shares at ${portfolio[stock_name]['price']:.2f} per share")
            sus = input("Would you like to still buy more shares, update how many shares you would like to buy, or exit (buy more, update, exit): ").replace(" ", "").lower()
            time.sleep(0.73)
            if sus == 'buymore':
                portfolio[stock_name]["shares"] += amount
            elif sus == 'update':
                amount = float(input('Enter the amount of shares you would like to invest: '))
                time.sleep(0.73)
                portfolio[stock_name]["shares"] = amount
            elif sus == 'exit':
                print("Alright, have a good day.")
                time.sleep(0.73)
                return
            else:
                print("Invalid option.")
                time.sleep(0.73)
                return
        elif wow == 'update':
            amount = float(input('Enter the amount of shares you would like to invest: '))
            time.sleep(0.73)
            portfolio[stock_name]["shares"] = amount
        elif wow == 'exit':
            print("Alright, have a good day.")
            time.sleep(0.73)
            return
        else:
            print("Invalid option.")
            time.sleep(0.73)
            return
    else:
        portfolio[stock_name] = {
            "shares": amount,
            "price": stock_price
        }
    
    accounts[name]["investment_portfolio"] = portfolio
    save_accounts(accounts)
    time.sleep(0.73)
    print(f"Added {amount} shares of {stock_name} at ${stock_price:.2f} per share to your investment portfolio.")
    time.sleep(0.73)




def remove_investment(name, accounts):
    portfolio = accounts[name].get("investment_portfolio", {})
    time.sleep(0.73)
    ticker_symbol = input("Enter the ticker symbol of the stock to remove: ").upper()
    time.sleep(0.73)

    if ticker_symbol in portfolio:
        stock = yf.Ticker(ticker_symbol)
        current_price = stock.history(period='1d')['Close'].iloc[0]

        shares = portfolio[ticker_symbol]["shares"]
        total_value = shares * current_price
        what = accounts[name]['balance']
        what = float(what) 
        what += total_value
        accounts[name]['balance'] = what

        del portfolio[ticker_symbol]

        save_accounts(accounts)
        time.sleep(0.73)
        print(f"Investment in {ticker_symbol} removed successfully.")
        time.sleep(0.73)
        print(f"Total value of ${total_value:.2f} added to your balance.")
        time.sleep(0.73)
    else:
        print(f"No investment found for ticker symbol: {ticker_symbol}")
        time.sleep(0.73)


def update_investment(name, accounts):
    if accounts[name].get('investment_portfolio') is None or not isinstance(accounts[name]['investment_portfolio'], dict):
        accounts[name]['investment_portfolio'] = {}
        time.sleep(0.73)
        print("Sorry, you have not purchased shares at the moment.")
        time.sleep(0.73)
        return
    time.sleep(0.73)
    stock_name = input("Enter the ticker symbol of the stock to update: ").upper()
    time.sleep(0.73)
    stock = yf.Ticker(stock_name)
    stock_price = stock.history(period='1d')['Close'].iloc[0]
    
    if stock_name in accounts[name].get('investment_portfolio', {}):
        time.sleep(0.73)
        wow = input(f"Would you like to check the price of {stock_name}? ").lower()
        time.sleep(0.73)

        
        if wow in positive_responses:
            time.sleep(0.73)
            print(f"The current price of the stock is ${stock_price:.2f}")
            time.sleep(0.73)
            how = input("Would you like to continue? ").lower()
            time.sleep(0.73)
            if how in positive_responses:
                pass
            elif how in negative_responses:
                time.sleep(0.73)
                print("Alright, have a great day!")
                time.sleep(0.73)
                return
            else:
                print("Invalid option.")
                time.sleep(0.73)
                return
        elif wow in negative_responses:
            pass
        else:
            print("Invalid option.")
            time.sleep(0.73)
            return
        time.sleep(0.73)
        amount = float(input("Enter the new amount of stock: "))
        time.sleep(0.73)
        accounts[name]['investment_portfolio'][stock_name] = {
            'shares': amount,
            'price': stock_price
        }
        save_accounts(accounts)
        time.sleep(0.73)
        print("Investment updated successfully.")
        time.sleep(0.73)
    else:
        print("Investment not found.")



def request_loan(accounts, name):
    loan_amount = float(input("Enter loan amount: "))
    time.sleep(0.73)
    if loan_amount <= 0:
        print("You have entered a negative number. ")
        time.sleep(0.73)
        return
    elif not isinstance(loan_amount, float):
        print("Sorry, you have entered an invalid amount.")
        time.sleep(0.73)
        return
    else:
        time.sleep(0.79)
        real_interest_rate = 12.18
        interest_rate = input("The interest rate is 12.18%. Are you ok with that? You have to pay back in 5 days: ")
        time.sleep(0.79)
        if interest_rate.lower() in positive_responses:
            total_amount_due = loan_amount * (1 + (real_interest_rate / 100))
            total_amount_due = float(total_amount_due)
            total_amount_due = round(total_amount_due, 2)
            accounts[name]["loan"] = {
                "amount": loan_amount,
                "interest_rate": real_interest_rate,
                "total_amount_due": total_amount_due,
                "remaining_balance": total_amount_due
            }
            what = accounts[name]['balance']
            what = float(what) 
            what += loan_amount
            accounts[name]['balance'] = what
            if accounts[name]['send_email']:
                message = f"""\
Subject: Loan Confirmation

Dear {accounts[name]['first_name']},

    You have just loaned ${loan_amount} with an interest rate of 12.18%.

    Hope you have a great day.

Regards,
    Manoj :)
                """
                receiver_email = accounts[name]['email']
                save_accounts(accounts)
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    time.sleep(0.79)
                    print("Loan created successfully.")
                    time.sleep(0.79)
                except Exception as e:
                    time.sleep(0.79)
                    print(f"Failed to send email: {e}")
                    time.sleep(0.79)
                finally:
                    server.quit()
                    return
            else:
                print("Loan request successful.")
                time.sleep(0.79)
                save_accounts(accounts)
        elif interest_rate.lower() in negative_responses:
            print("Alright")
            return
        else:
            print("Incorrect option")
            return




def repay_loan(accounts, name):
    if not accounts[name]['loans']:
        print("You have no loans to repay.")
        return
    loan_index = int(input("Enter the loan number you want to repay (starting from 1): ")) - 1
    if loan_index < 0 or loan_index >= len(accounts[name]['loans']):
        print("Invalid loan number.")
        return
    amount = float(input("Enter the amount you want to repay: "))
    amount = round(amount, 2)
    loan = accounts[name]['loans'][loan_index]
    if loan['status'] == 'pending':
        print("This loan is still pending approval.")
        return
    if amount >= loan['amount']:
        accounts[name]['loans'].pop(loan_index)
        save_accounts(accounts)
        print(f"Loan of {loan['amount']:.2f} fully repaid.")
    else:
        stuff = loan['amount']
        stuff = float(stuff)
        stuff -= amount
        loan['amount'] = stuff
        save_accounts(accounts)
        print(f"Partially repaid {amount:.2f}. Remaining loan amount is {loan['amount']:.2f}.")
def make_loan_payment(accounts, name):      
            
            if 'loan' not in accounts[name] or accounts[name]['loan'] is None or accounts[name]['loan']['remaining_balance'] <= 0:
                print("You do not have any loans at the moment.")
                return
            if accounts[name]['loan']['remaining_balance'] > 0: 
                what = accounts[name]['balance']
                time.sleep(0.79)
                print(f"You have {what} money left")
                time.sleep(0.79)
                how = accounts[name]['loan']['remaining_balance']
                print(f"You still owe {how} from the loan")
                time.sleep(0.79)
                try:
                    payment = float(input("Enter the payment amount: "))
                except ValueError:
                    time.sleep(0.79)
                    print("Invalid payment amount.")
                    return
                time.sleep(0.79)
                if payment <= 0:
                    time.sleep(0.79)
                    print("Payment amount must be positive.")
                elif payment > accounts[name]['balance']:
                    time.sleep(0.79)
                    print("You do not have enough money to pay for how much you would like to pay.")
                elif payment > (accounts[name]['loan']['remaining_balance']):
                    time.sleep(0.79)
                    print("Payment amount exceeds the money owed for the loan.")
                else:
                    what = (accounts[name]['loan']['remaining_balance'])
                    what = float(what)
                    what -= payment
                    amount = round(what, 2)
                    accounts[name]['loan']['remaining_balance'] = amount
                    accounts[name]['balance'] -= payment
                    time.sleep(0.79)
                    if accounts[name]['loan']['remaining_balance'] <= 0:
                        time.sleep(0.79)
                        print("Loan fully repaid!")
                    else:
                        print("Payment successful")
                    save_accounts(accounts)



def view_loan_status(accounts, name):
    if 'loan' in accounts[name]:
        if accounts[name]['send_email'] == True:
            wow = input("Would you like to get an email, or display or both of your loan status(email,display,both): ").lower()
            if wow == 'display':
                loan_info = accounts[name]["loan"]
                print("    Loan Status:   ")
                time.sleep(0.5)
                print(f"Loan Amount: {loan_info['amount']}")
                time.sleep(0.5)
                print(f"Interest Rate: {loan_info['interest_rate']}%")
                time.sleep(0.5)
                print(f"Total Amount You Borrowed: {loan_info['total_amount_due']}")
                time.sleep(0.5)
                print(f"Remaining Amount You have to pay: {loan_info['remaining_balance']}")
                time.sleep(0.5)
            elif wow == 'email':
                message = f"""\
Subject: Loan status
            
Dear {accounts[name]['first_name']},
            
            Loan Status:
   Loan Amount: {loan_info['amount']}
   Interest Rate: {loan_info['interest_rate']}%         
   Total Amount You Borrowed: {loan_info['total_amount_due']}
   Remaining Amount You have to pay: {loan_info['remaining_balance']}


    Hope you have a great day.
            
Regards,
   Manoj :)
                    """
                receiver_email = accounts[name]['email']
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    time.sleep(0.79)
                    print("Loan status successfully sent.")
                    time.sleep(0.79)
                except Exception as e:
                    time.sleep(0.79)
                    print(f"Failed to send email: {e}")
                    time.sleep(0.79)
                finally:
                    server.quit()
                    return
            elif wow == 'both':
                loan_info = accounts[name]["loan"]
                print("    Loan Status:   ")
                time.sleep(0.5)
                print(f"Loan Amount: {loan_info['amount']}")
                time.sleep(0.5)
                print(f"Interest Rate: {loan_info['interest_rate']}%")
                time.sleep(0.5)
                print(f"Total Amount You Borrowed: {loan_info['total_amount_due']}")
                time.sleep(0.5)
                print(f"Remaining Amount You have to pay: {loan_info['remaining_balance']}")
                time.sleep(0.5)
                message = f"""\
Subject: Loan status
            
Dear {accounts[name]['first_name']},
            
            Loan Status:
   Loan Amount: {loan_info['amount']}
   Interest Rate: {loan_info['interest_rate']}%         
   Total Amount You Borrowed: {loan_info['total_amount_due']}
   Remaining Amount You have to pay: {loan_info['remaining_balance']}


    Hope you have a great day.
            
Regards,
   Manoj :)
                    """
                receiver_email = accounts[name]['email']
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    time.sleep(0.79)
                    print("Loan status successfully sent. ")
                    time.sleep(0.79)
                except Exception as e:
                    time.sleep(0.79)
                    print(f"Failed to send email: {e}")
                    time.sleep(0.79)
                finally:
                    server.quit()
                    return
                
        else:   
            loan_info = accounts[name]["loan"]
            print("    Loan Status:   ")
            time.sleep(0.5)
            print(f"Loan Amount: {loan_info['amount']}")
            time.sleep(0.5)
            print(f"Interest Rate: {loan_info['interest_rate']}%")
            time.sleep(0.5)
            print(f"Total Amount You Borrowed: {loan_info['total_amount_due']}")
            time.sleep(0.5)
            print(f"Remaining Amount You have to pay: {loan_info['remaining_balance']}")
            time.sleep(0.5)
    else:
        time.sleep(0.5)
        print("No active loan.")




def transfer_between_accounts(accounts, name):
    from_account = name
    to_account = input("Enter the name of the account to transfer to: ")
    time.sleep(0.73)
    amount = float(input("Enter the amount to transfer: "))
    time.sleep(0.73)
    if amount <= 0:
        print("You have entered a negative number. ")
        time.sleep(0.73)
        return
    else:
        if to_account in accounts:
            if accounts[from_account]["balance"] >= amount:
                if accounts[name]['send_email'] == True:
                    message = f"""\
Subject: Transfer to another Account
                    
Dear {accounts[name]['first_name']},
                    
   You have just transfered ${amount} to {to_account}'s account

   Hope you have a great day.
                    
Regards,
   Manoj :)
                            """
                    receiver_email = accounts[name]['email']
                    try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.sendmail(sender_email, receiver_email, message)
                            time.sleep(0.79)
                            time.sleep(0.79)
                    except Exception as e:
                            time.sleep(0.79)
                            print(f"Failed to send email: {e}")
                            time.sleep(0.79)
                    finally:
                            server.quit()
                            return
                if accounts[to_account]['send_email'] == True:
                    message = f"""\
Subject: Transfer to another Account
                    
Dear {accounts[to_account]['first_name']},
                    
    {accounts[name]['first_name']} has just transfered ${amount} to your account.

    Hope you have a great day.
                    
Regards,
   Manoj :)
                            """
                    receiver_email = accounts[to_account]['email']
                    try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.sendmail(sender_email, receiver_email, message)
                            time.sleep(0.79)
                            time.sleep(0.79)
                    except Exception as e:
                            time.sleep(0.79)
                            print(f"Failed to send email: {e}")
                            time.sleep(0.79)
                    finally:
                            server.quit()
                            return
                why = accounts[from_account]["balance"]
                why = float(why)
                why -= amount
                accounts[from_account]["balance"] = why
                what = accounts[to_account]["balance"]
                what = float(what)
                what += amount
                accounts[to_account]["balance"] = what
                accounts[from_account]["transactions"].append({"type": "transfer_out", "amount": amount, "to": to_account})
                accounts[to_account]["transactions"].append({"type": "transfer_in", "amount": amount, "from": from_account})
                save_accounts(accounts)
                print(f"Successfully transferred ${amount} from {from_account} to {to_account}.")
            else:
                print("Insufficient balance.")
        else:
            print(f"There is no account named {to_account}.")



def forgot_password(accounts):
    batman = input("Whats the username of your account. ")
    if batman not in accounts:
        print("This username doesn't exist. ")
        return
    else: 
        cool_number = random.randint(100000, 999999)
        time.sleep(0.73)
        why = input(f"Is your email still {accounts[batman]['email']}: ").lower()
        time.sleep(0.73)
        if why in positive_responses:
            pass
        elif why in negative_responses:
            rizz = input('What is your current email? ')
            time.sleep(0.73)
            if rizz == accounts[batman]['email']:
                print("Hmm it seems that I have already displayed this email and you said no its not my current email, are you serious???? ")
                time.sleep(0.73)
                pass
            else:
                time.sleep(0.73)
                rizzy = input("What would you like your new email to be: ")
                time.sleep(0.73)
                accounts[batman]['email'] = rizzy
                save_accounts(accounts)
                pass
        receiver_email = accounts[batman]['email']
        message = f"""\
Subject: Password Reset
            
Dear {accounts[batman]['first_name']},
            
    Your randomly generated number is {cool_number}
    Please input this number in the website to change your password
            
    Hope you have a great day.
            
Regards,
    Manoj :)
                    """
        try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    time.sleep(0.79)
                    print("Randomly genrated number sent successfully. ")
                    time.sleep(0.79)
        except Exception as e:
                    time.sleep(0.79)
                    print(f"Failed to send email: {e}")
                    time.sleep(0.79)
        sus = int(input("Please enter the randomly generated number you have received in your email: "))
        while sus != cool_number:
                    sussy = input("Would you like to try again or exit: ").lower()
                    if sussy == 'try again' or 'tryagain':
                        sussy = input("Re enter the number: ").lower()
                    elif sussy == 'exit':
                        break
                    else:
                        print("Invalid Option ")
                        return
        if sus == cool_number:
                    how = input("What would you like your new password to be? ")
                    time.sleep(0.73)
                    if how == accounts[batman]['password']:
                        print("This is already your current password. ")
                        time.sleep(0.73)
                        son = input
                        wow = son("Would you like to change your password? ")
                        time.sleep(0.73)
                        if wow in positive_responses:
                            new_pass = son("What would you like your new password to be: ")
                            time.sleep(0.73)
                            accounts[batman]['password'] = new_pass
                            save_accounts(accounts)
                        elif wow in negative_responses:
                            print("Alright have a great day then. ")
                            time.sleep(0.73)
                            return
                        else:
                            print("Invalid Option ")
                            time.sleep(0.73)
                            return
                    else:
                        new_pass = son("What would you like your new password to be: ")
                        time.sleep(0.73)
                        accounts[batman]['password'] = new_pass
                        save_accounts(accounts)
        
        else:
            print("Sorry you have inputed an incorrect option. ")
            time.sleep(0.73)
            return

def update_budget_thing_sadly(accounts, name):
    skibidi = input("What is your budget password: ")
    time.sleep(0.73)
    while skibidi != accounts[name]['budget_password']:
        time.sleep(0.73)
        rizz = input("Would you like to reset password or try again: ").lower()
        time.sleep(0.73)
        if rizz == 'reset password':

            reset = input("What would you like your new budget password to be: ")
            time.sleep(0.73)
            accounts[name]['budget_password'] = reset
            save_accounts(accounts)
            skibidi = input("What is your budget password: ")
            time.sleep(0.73)
        elif rizz == 'try again' or 'tryagain':
            skibidi = input("What is your budget password: ")
            time.sleep(0.73)
        else:
            print("Sorry you have entered an invalid option. ")
            time.sleep(0.73)
            break
    if skibidi == accounts[name]['budget_password']:
        time.sleep(0.73)
        budget = float(input("How much would you like your budget to be. "))
        time.sleep(0.73)
        if budget <= 0:
            time.sleep(0.73)
            print("Sorry the number you have inputed is less than zero. ")
            time.sleep(0.73)
            return
        else:
            time.sleep(0.73)
            accounts[name]['budget'] = budget
            print(f"Your monthly budget is {budget} ")
            time.sleep(0.73)
            save_accounts(accounts)
            why = input(
                "Would you like to update your budget password: ").lower()
            time.sleep(0.73)
            if why in negative_responses:
                print("Alright have a good day. ")
                return
            elif why in positive_responses:
                budget_password = input("What would you like your new budget password to be: ")
                time.sleep(0.73)
                accounts[name]['budget_password'] = budget_password
                save_accounts(accounts)
            else:
                time.sleep(0.73)
                print("Invalid option ")
                return
def budget_thing(name, accounts):
    time.sleep(0.73)
    if accounts[name]['budget'] != 0:
        rizzy = input("Would you like to Add, View, or Update your budget(Add, View, Update): ").lower()
        time.sleep(0.73)
        if rizzy == 'view':
            print(f"Your current budget is {accounts[name]['budget']}")
            time.sleep(0.73)
            sus = input("Would you like to change your budget: ").lower()
            time.sleep(0.73)
            if sus in negative_responses:
                print("Alright have a great day. ")
                time.sleep(0.73)
                return
            elif sus in positive_responses:
                if accounts[name]['budget_password'] == None:
                    budget = float(input("How much would you like your new budget to be?: "))
                    time.sleep(0.73)
                    if budget <= 0:
                        print("Sorry the number you have inputed is less than zero. ")
                        time.sleep(0.73)
                        return
                    else:
                        accounts[name]['budget'] = budget
                        print(f"Your monthly budget is {budget} ")
                        time.sleep(0.73)
                        save_accounts(accounts)
                        why = input("Would you like to add a password to prevent overspending from your budget: ").lower()
                        time.sleep(0.73)
                        if why in negative_responses:
                            accounts[name]['budget_password'] = None
                            time.sleep(0.73)
                            return
                        elif why in positive_responses:
                            budget_password = input("What would you like your password to be. ")
                            time.sleep(0.73)
                            accounts[name]['budget_password'] = budget_password
                            time.sleep(0.73)
                            save_accounts(accounts)
                        else:
                            print("Invalid option ")
                            time.sleep(0.73)
                            return
                else:
                    update_budget_thing_sadly(accounts, name)
            else:
                print("Invalid option. ")
                time.sleep(0.73)
                return


        elif rizzy == 'add':
            if accounts[name]['budget'] != 0:
                time.sleep(0.73)
                wow = input("It seems like you already have a budget set would you like to update or view your current budget: ").lower()
                time.sleep(0.73)
                if wow == 'update':
                    if accounts[name]['budget_password'] == None:
                        budget = float(input("How much would you like your new budget to be. "))
                        time.sleep(0.73)
                        if budget <= 0:
                            print("Sorry the number you have inputed is less than zero. ")
                            time.sleep(0.73)
                            return
                        else: 
                            accounts[name]['budget'] = budget
                            print(f"Your monthly budget is {budget} ")
                            time.sleep(0.73)
                            save_accounts(accounts)
                            why = input(
                                "Would you like to add a password to prevent overspending from your budget: ").lower()
                            time.sleep(0.73)
                            if why in negative_responses:
                                accounts[name]['budget_password'] = None
                                return
                            elif why in positive_responses:
                                budget_password = input("What would you like your password to be. ")
                                time.sleep(0.73)
                                accounts[name]['budget_password'] = budget_password
                                save_accounts(accounts)
                            else:
                                print("Invalid option ")
                                time.sleep(0.73)
                                return
                    else:
                        update_budget_thing_sadly(accounts, name)
                elif wow == 'view':
                    print(f"Your current budget is {accounts[name]['budget']}")
                    time.sleep(0.73)
                    sus = input("Would you like to change your budget: ").lower()
                    time.sleep(0.73)
                    if sus in negative_responses:
                        print("Alright have a great day. ")
                        return
                    elif sus in positive_responses:
                        if accounts[name]['budget_password'] == None:
                            time.sleep(0.73)
                            budget = float(input("How much would you like your new budget to be. "))
                            time.sleep(0.73)
                            if budget <= 0:
                                print("Sorry the number you have inputed is less than zero. ")
                                time.sleep(0.73)
                                return
                            else:
                                accounts[name]['budget'] = budget
                                print(f"Your monthly budget is {budget} ")
                                time.sleep(0.73)
                                save_accounts(accounts)
                                why = input(
                                    "Would you like to add a password to prevent overspending from your budget: ").lower()
                                time.sleep(0.73)
                                if why in negative_responses:
                                    accounts[name]['budget_password'] = None
                                    time.sleep(0.73)
                                    return
                                elif why in positive_responses:
                                    budget_password = input("What would you like your password to be. ")
                                    time.sleep(0.73)
                                    accounts[name]['budget_password'] = budget_password
                                    time.sleep(0.73)
                                    save_accounts(accounts)
                                else:
                                    print("Invalid option ")
                                    time.sleep(0.73)
                                    return
                        else:
                            update_budget_thing_sadly(accounts, name)
                    else:
                        print("Invalid option. ")
                        time.sleep(0.73)
                        return
                else:
                    print("Invalid option. ")
                    time.sleep(0.73)
                    return
            else:
                budget = float(input("How much would you like your budget to be. "))
                time.sleep(0.73)
                if budget <= 0:
                    print("Sorry the number you have inputed is less than zero. ")
                    time.sleep(0.73)
                    return
                else: 
                    accounts[name]['budget'] = budget
                    print(f"Your monthly budget is {budget} ")
                    time.sleep(0.73)
                    save_accounts(accounts)
                    why = input("Would you like to add a password to go over the budget: ").lower()
                    time.sleep(0.73)
                    if why in negative_responses:
                        accounts[name]['budget_password'] = None
                        time.sleep(0.73)
                        return
                    elif why in positive_responses:
                        budget_password = input("What would you like your password to be. ")
                        time.sleep(0.73)
                        accounts[name]['budget_password'] = budget_password
                        save_accounts(accounts)
                    else:
                        print("Invalid option ")
                        time.sleep(0.73)
                        return
        elif rizzy == 'update':
            if accounts[name]['budget_password'] == None:
                time.sleep(0.73)
                budget = float(input("How much would you like your new budget to be. "))
                time.sleep(0.73)
                if budget <= 0:
                    print("Sorry the number you have inputed is less than zero. ")
                    time.sleep(0.73)
                    return
                else:
                    accounts[name]['budget'] = budget
                    print(f"Your monthly budget is {budget} ")
                    time.sleep(0.73)
                    save_accounts(accounts)
                    why = input(
                        "Would you like to add a password to prevent overspending from your budget: ").lower()
                    time.sleep(0.73)
                    if why in negative_responses:
                        accounts[name]['budget_password'] = None
                        time.sleep(0.73)
                        return
                    elif why in positive_responses:
                        budget_password = input("What would you like your password to be. ")
                        time.sleep(0.73)
                        accounts[name]['budget_password'] = budget_password
                        save_accounts(accounts)
                    else:
                        print("Invalid option ")
                        time.sleep(0.73)
                        return
            else:
                update_budget_thing_sadly(accounts, name)
        else:
            print("Invalid option. ")
            time.sleep(0.73)
            return
    else:
        wowies = float(input("How much would you like your budget to be? "))
        time.sleep(0.79)
        accounts[name]['budget'] = wowies
        print("Succesfully added your budget. ")
        time.sleep(0.72)
        sucks = input("Would you like to have a budget password? ").lower()
        time.sleep(0.74)
        save_accounts(accounts)
        while sucks not in positive_responses and sucks not in negative_responses:
            sucks = input("Invalid option please enter a valid option. ")
            time.sleep(0.23)
        if sucks in positive_responses:
            sussy = input("What would you like your budget password to be? ")
            time.sleep(0.72)
            accounts[name]['budget_password'] = sussy
            save_accounts(accounts)
            print("Succesfully added your budget password. ")
            time.sleep(0.72)
        elif sucks in negative_responses:
            print("Alright have a good day. ")
            return
    
        

def budget_password(accounts, name):
    time.sleep(0.73)
    how = input("Would you like to add, update, or delete your current(Delete, Update, Add): ").lower()
    time.sleep(0.73)
    if how == 'add':
        if accounts[name]['budget'] == 0:
            print("Sorry you do not have a budget to add a budget password, please add a budget first. ")
            time.sleep(0.73)
            return
        else:
            if accounts[name]['budget_password'] == None:
                time.sleep(0.73)
                why = input("What would you like your budget password to be ")
                time.sleep(0.73)
                accounts[name]['budget_password'] = why
            else:
                check = input("It seems like you already have a budget password would you like to view, update your current budget password or exit(View, Update, Exit): ").lower()
                time.sleep(0.73)
                if check == 'exit':
                    print('Alright have a great day. ')
                    time.sleep(0.73)
                    return
                elif check == 'view':
                    time.sleep(0.73)
                    checking = input(f'{accounts[name]['budget_password']} is your current budget password \n Would you like to exit or update it(Update, Exit)').lower()
                    time.sleep(0.73)
                    if checking == 'exit':
                        print("Alright have a great day. ")
                        return
                    elif checking == 'update':
                        time.sleep(0.73)
                        new_password = input("What would you like your new budget password to be ")
                        time.sleep(0.73)
                        accounts[name]['budget_password'] = new_password
                    else:
                        print("Invalid option") 
                        time.sleep(0.73)
                        return
                elif check == 'update':
                    skibidi = input("What is your current budget password: ")
                    time.sleep(0.73)
                    while skibidi != accounts[name]['budget_password']:
                        rizz = input("Would you like to reset password or try again: ").lower()
                        time.sleep(0.73)
                        if rizz == 'reset password':
                            reset = input("What would you like your new budget password to be: ")
                            time.sleep(0.73)
                            accounts[name]['budget_password'] = reset
                            save_accounts(accounts)
                            return
                        elif rizz == 'try again':
                            skibidi = input("What is your budget password: ")
                            time.sleep(0.73)
                        else:
                            print("Sorry you have entered an invalid option. ")
                            time.sleep(0.73)
                            return
                    if skibidi == accounts[name]['budget_password']:
                        new_password1 = input("What would you like your new budget password to be ")
                        time.sleep(0.73)
                        accounts[name]['budget_password'] = new_password1
                else:
                     print("Invalid option") 
                     time.sleep(0.73)
                     return
    elif how == 'delete':
        skibidi = input("What is your budget password: ")
        time.sleep(0.73)
        while skibidi != accounts[name]['budget_password']:
            rizz = input("Would you like to reset password or try again: ").lower()
            time.sleep(0.73)
            if rizz == 'reset password':
                reset = input("What would you like your new budget password to be: ")
                time.sleep(0.73)
                accounts[name]['budget_password'] = reset
                save_accounts(accounts)
                skibidi = input("What is your budget password: ")
                time.sleep(0.73)
            elif rizz == 'try again':
                skibidi = input("What is your budget password: ")
                time.sleep(0.73)
            else:
                print("Sorry you have entered an invalid option. ")
                time.sleep(0.73)
                break
        if skibidi == accounts[name]['budget_password']:
            nuh_uh = input("Would you like to delete your current budget password or exit(Delete, Exit): ").lower()
            time.sleep(0.73)
            if nuh_uh == 'delete':
                accounts[name]['budget_password'] = None
                print("Succesfully deleted your current budget password. ")
                time.sleep(0.73)
                return
            elif nuh_uh == 'exit':
                print("Alright have a great day. ")
                time.sleep(0.73)
                return
            else:
                print("Invalid option ")
                time.sleep(0.73)
                return
    elif how == 'update':
        if accounts[name]['budget_password'] == None:
            look = input("It seems like you don't currently have a budget password \n Would you like to add a password?: ").lower()
            time.sleep(0.73)
            if look in negative_responses:
                print("Alright have a great day. ")
                time.sleep(0.73)
                return
            elif look in positive_responses:
                whsy = input("What would you like your budget password to be ")
                time.sleep(0.73)
                accounts[name]['budget_password'] = whsy
            else:
                print("Invalid option ")
                time.sleep(0.73)
                return
        else:
            skibidi = input("What is your current budget password: ")
            time.sleep(0.73)
            while skibidi != accounts[name]['budget_password']:
                rizz = input("Would you like to reset password or try again: ").lower()
                time.sleep(0.73)
                if rizz == 'reset password':
                    reset = input("What would you like your new budget password to be: ")
                    time.sleep(0.73)
                    accounts[name]['budget_password'] = reset
                    save_accounts(accounts)
                    return
                elif rizz == 'try again':
                    skibidi = input("What is your budget password: ")
                    time.sleep(0.73)
                else:
                    print("Sorry you have entered an invalid option. ")
                    time.sleep(0.73)
                    return
            if skibidi == accounts[name]['budget_password']:
                new_password = input("What would you like your new budget password to be ")
                time.sleep(0.73)
                accounts[name]['budget_password'] = new_password
    else:
        print("Invalid option ")
        time.sleep(0.73)
        return


def add_funds_retirement(accounts, name):
    if 'retirement_balance' not in accounts[name]:
        accounts[name]['retirement_balance'] = 0.0

    amount = float(input("Enter the amount to add to your retirement account: "))
    time.sleep(0.79)
    accounts[name]['retirement_balance'] += amount
    save_accounts(accounts)
    print(f"Successfully added {amount} to your retirement account.")
    
def view_retirement_balance(accounts, name):
    if 'retirement_balance' not in accounts[name]:
        accounts[name]['retirement_balance'] = 0.0
        save_accounts(accounts)

    time.sleep(0.79)
    print(f"Your retirement account balance is: {accounts[name]['retirement_balance']}")
    time.sleep(0.7131)

def withdraw_funds_retirement(accounts, name):
    if 'retirement_balance' not in accounts[name]:
        accounts[name]['retirement_balance'] = 0.0
        save_accounts(accounts)

    if accounts[name]['retirement_balance'] == 0.0:
        time.sleep(0.79)
        print("You do not have enough money to withdraw any money.")
        return

    amount = float(input("Enter the amount to withdraw from your retirement account: "))
    penalty = amount * 0.10  

    if accounts[name]['retirement_balance'] >= amount + penalty:
        stuff = accounts[name]['retirement_balance']
        stuff = float(stuff)
        stuff -= (amount + penalty)
        accounts[name]['retirement_balance'] = stuff
        save_accounts(accounts)
        print(f"Successfully withdrew {amount} from your retirement account with a {penalty} penalty.")
    else:
        print("Insufficient funds in your retirement account.")
def get_exchange_rate(target_currency):
    try:
        response = requests.get(f'{BASE_URL}/{API_KEY}/latest/USD')
        data = response.json()
        return data['conversion_rates'][target_currency.upper()]
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return None

def convert_currency(accounts, name):
    try:
        current_balance = Decimal(accounts[name]["balance"]) 
    except (InvalidOperation, ValueError):
        print("Error: Invalid current balance.")
        return

    try:
        money = Decimal(input("How much money would you like to convert (U.S. dollars): "))
    except (InvalidOperation, ValueError):
        print("Error: Invalid amount entered.")
        return

    time.sleep(0.73)
    if money <= 0:
        print("Sorry, the number you have inputted is less than zero.")
        time.sleep(0.73)
        return

    if money > current_balance:
        print("Sorry, you do not have enough to cover the transfer.")
        time.sleep(0.73)
        return

    wowie_fr = Decimal('0.04')
    wowie = input("There is a 4% fee for currency transferring. Would you still like to transfer your currency?: ").lower()
    time.sleep(0.73)
    if wowie in negative_responses:
        print("Alright, have a good day!")
        time.sleep(0.73)
        return
    elif wowie in positive_responses:
        money_fr = money * wowie_fr
        money_frfr = money_fr + money
        if money_frfr > current_balance:
            print("Sorry, you do not have enough money to pay for the transfer and the fee.")
            time.sleep(0.73)
            return

        target_currency = input("Which currency would you like to convert your balance to? (INR, EUR, GBP). Please use the national 3-letter abbreviations: ").upper()
        time.sleep(0.73)

        exchange_rate = get_exchange_rate(target_currency)
        if not exchange_rate:
            print("Failed to fetch the exchange rate.")
            time.sleep(0.73)
            return

        try:
            exchange_rate = Decimal(exchange_rate)
        except (InvalidOperation, ValueError):
            print("Error: Invalid exchange rate.")
            return

        new_balance = current_balance - money_frfr
        accounts[name]["balance"] = str(new_balance) 
        time.sleep(0.5)

        converted_money = money * exchange_rate
        if "converted_balances" not in accounts[name]: 
            accounts[name]["converted_balances"] = []

        accounts[name]['converted_balances'].append({
            "Currency type": target_currency,
            "Amount": str(converted_money) 
        })
        print(f"Converted amount: {converted_money:.2f}")
        print(f"New balance: {new_balance}")
        
        with open('minerstuff.json', 'r') as file:
            data = file.read()
            if not data:
                all_results = {}
            else:
                all_results = json.loads(data)

        if name not in all_results:
            all_results[name] = {"converted_balances": []}

        all_results[name]["converted_balances"].append({
            "Currency type": target_currency,
            "Amount": str(converted_money)
        })

        with open('minerstuff.json', 'w') as file:
            json.dump(all_results, file, indent=4)

        print("Updated your balance.")
        time.sleep(0.79)
    else:
        print("Invalid option.")
        time.sleep(0.73)
        return



        


def sign_in(accounts, name, password):
    if name in accounts and accounts[name]["password"] == password:
        time.sleep(0.79)
        print(f"Welcome back, {name}")
        time.sleep(0.79)
        if 101 <= accounts[name]["balance"] <= 1000:
            print(f"You have only {accounts[name]['balance']} dollars left")
        elif 1 <= accounts[name]['balance'] <= 100:
            print(f"You have barely only {accounts[name]['balance']} dollars left")
        elif accounts[name]['balance'] == 0:
            print("Ur broke :) ")
        time.sleep(0.79)

        def deposit(amount1):
            if amount1 <= 0:
                print("Sorry, the number you have inputted is less than or equal to zero.")
                time.sleep(0.73)
                return
            stuff = accounts[name]["balance"]
            stuff = float(stuff)
            stuff += amount1
            accounts[name]["balance"] = stuff
            print("Deposit successful.")
            time.sleep(0.73)
            print(f"Your current balance is ${accounts[name]['balance']}")
            time.sleep(0.73)
            accounts[name]["transactions"].append({"type": "deposit", "amount": amount1})
            save_accounts(accounts)


            if accounts[name].get('send_email'):
                message = f"""\
        Subject: Deposit

Dear {accounts[name]['first_name']},

    You have just deposited ${amount1}.

    Hope you have a great day.

Regards,
    Manoj :)
        """
                receiver_email = accounts[name]['email']
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    print("Email sent successfully.")
                except Exception as e:
                    print(f"Failed to send email: {e}")
                finally:
                    server.quit()  

        def apply_loan(accounts, name):
            request_loan(accounts, name)

        def repay_loan(accounts, name):
            make_loan_payment(accounts, name)

        def view_loan(accounts, name):
            view_loan_status(accounts, name)

        def load_accounts(filename):
            try:
                with open(filename, 'r') as f:
                    data = f.read().strip()
                    if not data:
                        return {}  
                    return json.loads(data)
            except FileNotFoundError:
                print(f"File {filename} not found.")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")
            return {}

        def check_balance(name, accounts):
            accountsy = load_accounts('minerstuff.json')
            if name not in accountsy:
                if accounts[name]['send_email']:
                    time.sleep(0.79)
                    askin = input("Would you like to get an email, display, or both of your balance (email, display, both): ").lower()

                    balance = accounts[name]["balance"]

                    if askin == 'display' or askin == 'both':
                        print("Your U.S. balance is:", balance)
                        time.sleep(0.79)
                        if balance == 0:
                            print("You're broke :)")
                            time.sleep(0.79)


                    if askin == 'email' or askin == 'both':

                        message = f"""\
            Subject: Account Balance

    Dear {accounts[name]['first_name']},

        You have ${balance},

        Hope you have a great day.

    Regards,
        Manoj :)
            """
                        receiver_email = accounts[name]['email']


                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.sendmail(sender_email, receiver_email, message)
                            time.sleep(0.79)
                            print("Email sent successfully.")
                        except Exception as e:
                            print(f"Failed to send email: {e}")
                        finally:
                            server.quit()

                else:
                    balance = accounts[name]["balance"]
                    converted_balances = accounts[name].get('converted_balances', [])
                    print("Your U.S. balance is:", balance)
                    time.sleep(0.79)
                    if balance == 0:
                        print("You're broke :)")
                        time.sleep(0.79)
                    if converted_balances:
                        print("Converted Balances:")
                        for converted in converted_balances:
                            print(f"Currency: {converted['Currency type']}, Amount: {float(converted['Amount']):.2f}")
                            time.sleep(0.79)
                    return
                return
            
            if accounts[name]['send_email']:
                askin = input("Would you like to get an email, display, or both of your balance (email, display, both): ").lower()

                balance = accounts[name]["balance"]
                converted_balances = accountsy[name].get('converted_balances', [])

                if askin == 'display' or askin == 'both':
                    print("Your U.S. balance is:", balance)
                    time.sleep(0.79)
                    if balance == 0:
                        print("You're broke :)")
                        time.sleep(0.79)
                    if converted_balances:
                        print("Converted Balances:")
                        for converted in converted_balances:
                            converted_fr = float(converted['Amount'])
                            print(f"Currency: {converted['Currency type']}, Amount: {converted_fr:.2f}")
                            time.sleep(0.79)

                if askin == 'email' or askin == 'both':
                    if converted_balances:
                        message = f"""\
        Subject: Account Balance

Dear {accounts[name]['first_name']},

    You have ${balance}.
    {"".join([f"Currency: {converted['Currency type']}, Amount: {float(converted['Amount']):.2f}\n" for converted in converted_balances])}

    Hope you have a great day.

Regards,
    Manoj :)
        """
                    else:
                        message = f"""\
        Subject: Account Balance

Dear {accounts[name]['first_name']},

    You have ${balance},

    Hope you have a great day.

Regards,
    Manoj :)
        """
                    receiver_email = accounts[name]['email']


                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(sender_email, sender_password)
                        server.sendmail(sender_email, receiver_email, message)
                        time.sleep(0.79)
                        print("Email sent successfully.")
                    except Exception as e:
                        print(f"Failed to send email: {e}")
                    finally:
                        server.quit()

            else:
                balance = accounts[name]["balance"]
                converted_balances = accounts[name].get('converted_balances', [])
                print("Your U.S. balance is:", balance)
                time.sleep(0.79)
                if balance == 0:
                    print("You're broke :)")
                    time.sleep(0.79)
                if converted_balances:
                    print("Converted Balances:")
                    for converted in converted_balances:
                        print(f"Currency: {converted['Currency type']}, Amount: {float(converted['Amount']):.2f}")
                        time.sleep(0.79)
                
        def send_email(receiver_email, subject, body):
            try:
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                message = f"Subject: {subject}\n\n{body}"
                server.sendmail(sender_email, receiver_email, message)
            except Exception as e:
                print(f"Failed to send email: {e}")
            finally:
                server.quit()

        def transaction_history(accounts, name):
            try:
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT * FROM transactions WHERE account_name = %s", (name,))
                user_transactions = cursor.fetchall()
                cursor.close()
                connection.close()

                transaction_details = ""
                for transaction in user_transactions:
                    try: 
                        if transaction['type'] == 'withdrawal':
                            if 'fee' in transaction == None:
                                transaction_details += f"Withdrawal: ${transaction['amount']}\n"
                            else:
                                transaction_details += f"Withdrawal: ${transaction['amount']}, Fee: ${transaction['fee']:.2f}\n"
                    except TypeError:
                        pass
                    if transaction['type'] == 'deposit':
                        transaction_details += f"Deposit: ${transaction['amount']}\n"
                    elif transaction['type'] == 'investment':
                        transaction_details += f"Investment: ${transaction['amount']}\n"
                    else:
                        pass

                if accounts[name]['send_email']:
                    askin = input("Would you like to get an email, display, or both of your transactions (email, display, both): ").lower()
                    if askin == 'email':
                        message_body = f"""\
Dear {accounts[name]['first_name']},

You have ${accounts[name]['balance']}.
{transaction_details}

Hope you have a great day.

Regards,
    Manoj :)"""
                        send_email(accounts[name]['email'], "Transactions", message_body)
                        return
                    elif askin == 'display' or askin == 'both':
                        print("Transaction History: \n")
                        print(transaction_details)
                        if askin == 'both':
                            message_body = f"""\
Dear {accounts[name]['first_name']},

    You have ${accounts[name]['balance']}.
    {transaction_details}

    Hope you have a great day.

Regards,
    Manoj :)"""
                            send_email(accounts[name]['email'], "Transactions", message_body)
                    else:
                        print("Invalid option")
                        return

                else:
                    print("Transaction History:")
                    print(transaction_details)

            except mysql.connector.Error as err:
                print(f"Error: {err}")
            

        def withdraw(amount, accounts, name, sender_email, sender_password, negative_responses, positive_responses):
            def checkbudget_forwithdraw(amount, accounts, name):
                if amount <= 0:
                    print("Sorry, the number you have inputted is less than or equal to zero.")
                    time.sleep(0.73)
                    return

                if amount > accounts[name]["balance"]:
                    print("Don't have enough money.")
                    time.sleep(0.73)
                    return

                if accounts[name]['budget'] == 0:
                    stuff = accounts[name]["balance"]
                    stuff = float(stuff)
                    stuff -= amount
                    accounts[name]["balance"] = stuff
                    print(f"Withdrew ${amount}.")
                    time.sleep(0.73)
                    accounts[name]["transactions"].append({"type": "withdrawal", "amount": amount})
                    save_accounts(accounts)
                    return

                if amount > accounts[name]["budget"]:
                    if accounts[name]['budget_password'] is None:
                        sus = input("Are you sure you would like to withdraw this amount because it goes over your budget?: ").lower()
                        time.sleep(0.73)
                        if sus in negative_responses:
                            print("Alright, have a great day.")
                            time.sleep(0.73)
                            return
                        elif sus in positive_responses:
                            stuff = accounts[name]["balance"]
                            stuff = float(stuff)
                            stuff -= amount
                            accounts[name]["balance"] = stuff
                            print(f"Withdrew ${amount}.")
                            time.sleep(0.73)
                            accounts[name]["transactions"].append({"type": "withdrawal", "amount": amount})
                            save_accounts(accounts)
                            return
                    else:
                        skibidi = input("What is your budget password: ")
                        time.sleep(0.73)
                        while skibidi != accounts[name]['budget_password']:
                            rizz = input("Would you like to reset the password, try again, or exit? ").lower()
                            time.sleep(0.73)
                            if rizz == 'reset password':
                                reset = input("What would you like your new budget password to be: ")
                                time.sleep(0.73)
                                accounts[name]['budget_password'] = reset
                                save_accounts(accounts)
                                skibidi = input("What is your budget password: ")
                                time.sleep(0.73)
                            elif rizz in ['try again', 'tryagain']:
                                skibidi = input("What is your budget password: ")
                                time.sleep(0.73)
                            elif rizz == 'exit':
                                print("Alright, have a great day.")
                                time.sleep(0.73)
                                return
                            else:
                                print("Sorry, you have entered an invalid option.")
                                time.sleep(0.73)
                                return
                        stuff = accounts[name]["balance"]
                        stuff = float(stuff)
                        stuff -= amount
                        accounts[name]["balance"] = stuff
                        print(f"Withdrew ${amount}.")
                        time.sleep(0.73)
                        accounts[name]["transactions"].append({"type": "withdrawal", "amount": amount})
                        save_accounts(accounts)
                        return

            checkbudget_forwithdraw(amount, accounts, name)

            if accounts[name]['send_email']:
                message = f"""\
        Subject: Withdrawal

Dear {accounts[name]['first_name']},

    You withdrew ${amount}.

    Hope you have a great day.

Regards,
    Manoj :)
        """
                receiver_email = accounts[name]['email']
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    time.sleep(0.79)
                except Exception as e:
                    time.sleep(0.79)
                    print(f"Failed to send email: {e}")
                    time.sleep(0.79)
                finally:
                    server.quit()



        def withdraw_sav(amount2, accounts, name, sender_email, sender_password, negative_responses, positive_responses):
            def checkbudget_forwithdraw_sav(amount2, accounts, name):
                fee = amount2 * 0.05
                total_withdrawal = amount2 + fee
                time.sleep(0.73)
                
                if amount2 <= 0:
                    print("Sorry, the number you have input is less than zero.")
                    time.sleep(0.73)
                    return
                
                if amount2 > accounts[name]["balance"]:
                    print("Don't have enough money to cover the withdrawal.")
                    time.sleep(0.73)
                    return
                
                if accounts[name]['budget'] == 0:
                    stuff = accounts[name]["balance"]
                    stuff = float(stuff)
                    stuff -= total_withdrawal
                    accounts[name]["balance"] = stuff
                    time.sleep(0.79)
                    print(f"Withdrew ${amount2}. A 5% fee of ${fee:.2f} has been applied.")
                    time.sleep(0.79)
                    accounts[name]["transactions"].append({"type": "withdrawal", "amount": amount2, "fee": fee})
                    save_accounts(accounts)
                    return
                
                if total_withdrawal > accounts[name]["budget"]:
                    if accounts[name]['budget_password'] is None:
                        sus = input("Are you sure you would like to withdraw this amount because it goes over your budget? ").lower()
                        time.sleep(0.73)
                        if sus in negative_responses:
                            print("Alright, have a great day.")
                            time.sleep(0.73)
                            return
                        elif sus in positive_responses:
                            stuff = accounts[name]["balance"]
                            stuff = float(stuff)
                            stuff -= total_withdrawal
                            accounts[name]["balance"] = stuff
                            time.sleep(0.79)
                            print(f"Withdrew ${amount2}. A 5% fee of ${fee:.2f} has been applied.")
                            time.sleep(0.79)
                            accounts[name]["transactions"].append({"type": "withdrawal", "amount": amount2, "fee": fee})
                            save_accounts(accounts)
                            return
                    else:
                        skibidi = input("What is your budget password: ")
                        time.sleep(0.73)
                        while skibidi != accounts[name]['budget_password']:
                            rizz = input("Would you like to reset the password, try again, or exit? ").lower()
                            time.sleep(0.73)
                            if rizz == 'reset password':
                                reset = input("What would you like your new budget password to be? ")
                                time.sleep(0.73)
                                accounts[name]['budget_password'] = reset
                                save_accounts(accounts)
                                skibidi = input("What is your budget password: ")
                                time.sleep(0.73)
                            elif rizz in ['try again', 'tryagain']:
                                skibidi = input("What is your budget password: ")
                                time.sleep(0.73)
                            elif rizz == 'exit':
                                print("Alright, have a great day.")
                                time.sleep(0.73)
                                return
                            else:
                                print("Sorry, you have entered an invalid option.")
                                time.sleep(0.73)
                                return
                        stuff = accounts[name]["balance"]
                        stuff = float(stuff)
                        stuff -= total_withdrawal
                        accounts[name]["balance"] = stuff
                        time.sleep(0.79)
                        print(f"Withdrew ${amount2}. A 5% fee of ${fee:.2f} has been applied.")
                        time.sleep(0.79)
                        accounts[name]["transactions"].append({"type": "withdrawal", "amount": amount2, "fee": fee})
                        save_accounts(accounts)
            
            checkbudget_forwithdraw_sav(amount2, accounts, name)
            
            if accounts[name]['send_email']:
                message = f"""\
        Subject: Withdrawal

Dear {accounts[name]['first_name']},

    You withdrew ${amount2} with a 5% fee.

    Hope you have a great day.

Regards,
    Manoj :)
        """
                receiver_email = accounts[name]['email']
                try:
                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(sender_email, sender_password)
                    server.sendmail(sender_email, receiver_email, message)
                    time.sleep(0.79)
                except Exception as e:
                    time.sleep(0.79)
                    print(f"Failed to send email: {e}")
                    time.sleep(0.79)
                finally:
                    server.quit()



        def check_personal():
            user_info = accounts[name]
            for key, value in user_info.items():
                if key != "password" and key != 'transactions' and key != 'converted_balances' and key != 'loan_amount' and key != 'interest_rate' and key != 'total_amount_due' and key != 'remaining_balance' and key != 'budget' and key != 'budget_password' and key !=  'send_email' and key != 'investment_portfolio' and key != 'loan':
                    print(f"{key}: {value}")
                    time.sleep(0.79)
            if not accounts[name]['send_email']:
                how = input("Would you like to get email updates for withdrawals, deposits, etc.: ").lower()
                time.sleep(0.73)
                if how in positive_responses:
                    accounts[name]['send_email'] = True
                    print("Succesfully updated send email ")
                    time.sleep(0.73)
                    save_accounts(accounts)
                    return
                elif how in negative_responses:
                    accounts[name]['send_email'] = None
                    save_accounts(accounts)
                    time.sleep(0.74)
                    return
                else:
                    print("Invalid Option ")
                    time.sleep(0.73)
                    return



        def update_personal():
            thing = input("Enter the name of the field you would want to update: ")
            time.sleep(0.73)
            if thing != "password" and thing != 'balance':
                if thing in accounts[name]:
                    new_value = input(f"Enter the new value for {thing}: ")
                    time.sleep(0.73)
                    if new_value == accounts[name][thing]:
                        print(f"Your {thing} is already {new_value} ")
                        time.sleep(0.73)
                        return
                    else:
                        accounts[name][thing] = new_value
                        time.sleep(0.79)
                        print(f"Updated {thing} for account {name}.")
                        save_accounts(accounts)
                        if accounts[name]['send_email'] == True:
                            receiver_email = accounts[name]['email']
                            message = f"""\
    Subject: Updating Personal

Dear {accounts[name]['first_name']},

    Your {thing} has been updated to: {new_value}

    Hope you have a great day.

Regards,
    Manoj :)
                                """
                            try:
                                server = smtplib.SMTP('smtp.gmail.com', 587)
                                server.starttls()
                                server.login(sender_email, sender_password)
                                server.sendmail(sender_email, receiver_email, message)
                                time.sleep(0.79)
                                print(f"Succesfully updated {thing}.")
                                time.sleep(0.79)
                            except Exception as e:
                                time.sleep(0.79)
                                print(f"Failed to send email: {e}")
                                time.sleep(0.79)
                            finally:
                                server.quit()
                                return
                        else: 
                            print(f"Succesfully updated {thing}.")     
                            time.sleep(0.73)
                else:
                    print(f"Field {thing} does not exist for account {name}.")
                    time.sleep(0.73)
            else:
                print(f"Sorry, cannot update {thing} here")
                time.sleep(0.73)
                return

        def update_password():
            wow = input("Would you like to change your password?: ").lower()
            time.sleep(0.73)
            random_rumber = random.randint(100000, 999999)
            if wow in positive_responses:
                how = input("What is your current password: ")
                time.sleep(0.73)
                if how == accounts[name]['password']:
                        message = f"""\
Subject: Password Change

Dear {accounts[name]['first_name']},

   Your 6 Random digit number is {random_rumber}.

    Hope you have a great day.

Regards,
    Manoj :)
                    """

                        receiver_email = accounts[name]['email']
                        try:
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(sender_email, sender_password)
                            server.sendmail(sender_email, receiver_email, message)
                            time.sleep(0.79)
                        except Exception as e:
                            time.sleep(0.79)
                            print(f"Failed to send email: {e}")
                            time.sleep(0.79)
                        nah_uh = int(input("What is the random 6 digit number sent to you via email? "))
                        time.sleep(0.73)
                        while nah_uh != random_rumber:
                            wowie = input("Would you like to try again or exit. ")
                            time.sleep(0.73)
                            if wowie == 'tryagain' or 'try again':
                                nah_uh = input("What is the random 6 digit number sent to you via email? ")
                                time.sleep(0.73)
                            elif wowie == 'exit':
                                print("Alright have a great day! ")
                                time.sleep(0.73)
                                break
                        if nah_uh == random_rumber:
                            change = input("What would you like your new password to be, must be atleast 8 characters: ")
                            while change < 8:
                                time.sleep(0.72)
                                change = input("Your password was under 8 letters, could you please type another password that is above 8 characters: ")
                            time.sleep(0.73)
                            if change == accounts[name]['password']:
                                wat = input("This is already your current password, would you like to change your password or keep this password? ")
                                if wat == 'change':
                                    change = input("What would you like your new password to be: ")
                                    re_do_change = input("Re-enter the new password: ")
                                    time.sleep(0.73)
                                    while change != re_do_change:
                                        print("Passwords do not match. Please try again.")
                                        time.sleep(0.73)
                                        re_do_change = input("Re-enter the new password: ")
                                        time.sleep(0.73)
                                    accounts[name]['password'] = re_do_change
                                    time.sleep(0.78)
                                    print("Password updated successfully.")
                                    time.sleep(0.73)
                                    save_accounts(accounts)
                                elif wat == 'keep':
                                    print("Alright have a great day. ")
                                    return
                                else:
                                    print("Invalid Option. ")
                                    return
                            else:
                                re_do_change = input("Re-enter the new password: ")
                                time.sleep(0.73)
                                while change != re_do_change:
                                    print("Passwords do not match. Please try again.")
                                    time.sleep(0.73)
                                    re_do_change = input("Re-enter the new password: ")
                                    time.sleep(0.73)
                                accounts[name]['password'] = re_do_change
                                time.sleep(0.78)
                                print("Password updated successfully.")
                                time.sleep(0.73)
                                save_accounts(accounts)
                else:
                    print("Incorrect current password.")
                    time.sleep(0.73)
            elif wow in negative_responses:
                print("Alright have a great day! ")
                time.sleep(0.73)
                return
            else:
                print("Invalid option ")
                time.sleep(0.73)
                return

        def delete_acc():
            what = input("What's the name of your account: ")
            time.sleep(0.73)
            if what not in accounts:
                print("Account not found.")
                time.sleep(3)
                return
            else:
                time.sleep(2.5)
                sus = input("What is your current password for this account: ")
                time.sleep(0.73)
                while sus != accounts[name]['password']:
                    skibidi = input("Would you like to exit or try again(Exit or Try Again): ").lower().strip()
                    time.sleep(0.73)
                    if skibidi == 'try again' or 'tryagain':
                        time.sleep(0.73)
                        sus = input("What is your current password for this account: ")
                        time.sleep(0.73)
                    elif skibidi == 'exit':
                        time.sleep(0.73)
                        print("Alright have a great day. ")
                        time.sleep(0.73)
                        return
                    else:
                        print("Invalid option ")
                        time.sleep(0.73)
                if sus == accounts[name]['password']:        
                    why = input("Would you like to delete your account (cannot be changed)?: ").lower()
                    time.sleep(0.73)
                    if why in positive_responses:
                        how = input("Are you sure?: ").lower()
                        time.sleep(0.73)
                        if how in positive_responses:
                            if accounts[what]['send_email'] == True:
                                receiver_email = accounts[what]['email']
                                message = f"""\
Subject: Deleted Account

Dear {accounts[what]['first_name']},

    Your account has just been deleted.

    Hope you have a great day.

Regards,
    Manoj :)
                                """
                                try:
                                    server = smtplib.SMTP('smtp.gmail.com', 587)
                                    server.starttls()
                                    server.login(sender_email, sender_password)
                                    server.sendmail(sender_email, receiver_email, message)
                                    time.sleep(0.79)
                                    print(f"Succesfully Deleted Account.")
                                    time.sleep(0.79)
                                    del accounts[what]
                                    save_accounts(accounts)
                                except Exception as e:
                                    time.sleep(0.79)
                                    print(f"Failed to send email: {e}")
                                    time.sleep(0.79)
                                finally:
                                    server.quit()
                                    return
                            else:
                                del accounts[what]
                                save_accounts(accounts)
                                print("Account deleted successfully.")
                                time.sleep(0.73)
                        elif how in negative_responses:
                            print("Alright have a great day. ")
                            time.sleep(0.73)
                            return
                        else:
                            print("Invalid option ")
                            time.sleep(0.73)
                            return
                    elif why in negative_responses:
                        print("Alright. ")
                        time.sleep(0.73)
                        return
                    else:
                        print("Invalid option ")
                        time.sleep(0.73)
                        return
                

        if accounts[name]["account_type"] == 'checking':
            while True:
                check_money = int(input(
                    "Would you like to: 1. Check your balance, 2. Withdraw money, 3. Deposit money, 4. View personal information, 5. Update personal information, 6. View transaction history, 7. Delete Account, 8. Update password, 9. Apply for a loan, 10. Repay a loan, 11. View loan status, 12. Currency Exchange, 13. Transfer Money To Another Account, 14. Add/View/Delete a budget, 15. Add/Delete/View a budget password, 16 Exit: "))
                time.sleep(0.73)
                if check_money == 1:
                    check_balance(name, accounts)
                elif check_money == 2:
                    time.sleep(0.79)
                    amount = float(input("How much would you like to withdraw: "))
                    time.sleep(0.79)
                    withdraw((amount, accounts, name, sender_email, sender_password, negative_responses, positive_responses))
                elif check_money == 3:
                    time.sleep(0.79)
                    amount1 = float(input("How much would you like to deposit: "))
                    time.sleep(0.79)
                    deposit(amount1)
                elif check_money == 4:
                    time.sleep(0.79)
                    check_personal()
                elif check_money == 5:
                    time.sleep(0.79)
                    update_personal()
                elif check_money == 6:
                    time.sleep(0.79)
                    transaction_history(accounts, name)
                elif check_money == 7:
                    time.sleep(0.79)
                    delete_acc()
                    break
                elif check_money == 8:
                    update_password()
                elif check_money == 9:
                    time.sleep(0.79)
                    apply_loan(accounts, name)
                elif check_money == 10:
                    time.sleep(0.79)
                    repay_loan(accounts, name)
                elif check_money == 11:
                    time.sleep(0.79)
                    view_loan(accounts, name)
                elif check_money == 12:
                    time.sleep(0.79)
                    convert_currency(accounts, name)
                elif check_money == 13:
                    time.sleep(0.79)
                    transfer_between_accounts(accounts, name)
                elif check_money == 14:
                    time.sleep(0.79)
                    budget_thing(name, accounts)
                elif check_money == 15:
                    budget_password(accounts, name)
                elif check_money == 16:
                    time.sleep(0.79)
                    break
                else:
                    time.sleep(0.79)
                    print("Invalid option.")
                    time.sleep(0.73)


        elif accounts[name]["account_type"] == "saving":
            while True:
                check_money = int(input(
                    "Would you like to: 1. Check your balance, 2. Withdraw money (5% fee), 3. Deposit money, 4. View personal information, 5. Update personal information, 6. View transaction history, 7. Delete Account, 8. Update password, 9. Apply for a loan, 10. Repay a loan, 11. View loan status, 12. Currency Exchange, 13. Transfer Money To Another Account, 14. Add/View/Delete a budget, 15. Add/Delete/View a budget password, 16 Exit: "))
                time.sleep(0.73)
                if check_money == 1:
                    time.sleep(0.79)
                    check_balance(name, accounts)
                    time.sleep(0.79)
                elif check_money == 2:
                    time.sleep(0.79)
                    amount2 = float(input("How much would you like to withdraw (note there is a 5% deduction): "))
                    time.sleep(0.79)
                    withdraw_sav(amount2, accounts, name, sender_email, sender_password, negative_responses, positive_responses)
                elif check_money == 3:
                    time.sleep(0.79)
                    amount1 = float(input("How much would you like to deposit: "))
                    time.sleep(0.79)
                    deposit(amount1)
                elif check_money == 4:
                    time.sleep(0.79)
                    check_personal()
                elif check_money == 5:
                    time.sleep(0.79)
                    update_personal()
                elif check_money == 6:
                    time.sleep(0.79)
                    transaction_history(accounts, name)
                elif check_money == 7:
                    time.sleep(0.79)
                    delete_acc()
                    break
                elif check_money == 8:
                    update_password()
                elif check_money == 9:
                    time.sleep(0.79)
                    apply_loan(accounts, name)
                elif check_money == 10:
                    time.sleep(0.79)
                    repay_loan(accounts, name)
                elif check_money == 11:
                    time.sleep(0.79)
                    view_loan(accounts, name)
                elif check_money == 12:
                    time.sleep(0.79)
                    convert_currency(accounts, name)
                elif check_money == 13:
                    time.sleep(0.79)
                    transfer_between_accounts(accounts, name)
                elif check_money == 14:
                    time.sleep(0.79)
                    budget_thing(name, accounts)
                elif check_money == 15:
                    budget_password(accounts, name)
                elif check_money == 16:
                    time.sleep(0.79)
                    break
                else:
                    time.sleep(0.79)
                    print("Invalid option.")
        elif accounts[name]["account_type"] == "investment":
            time.sleep(0.73)
            while True:
                how = input("Would you like to 1. Add an Investment, 2. View your Investments, 3. Delete your Investments, 4. Update your Investments, 5. Check your Balance, 6. Apply for a loan, 7. Repay a loan, 8. View loan status, 9. Withdraw money, 10. Deposit money, 11. View personal information, 12. Update personal information, 13. View transaction history, 14. Delete Account, 15. Update password, 16. Currency Exchange, 17. Transfer Money To Another Account, 18. Exit: ")
                time.sleep(0.73)
                if how == '1':
                    add_investment(name, accounts)
                elif how == '2':
                    view_investments(name, accounts)
                elif how == '3':
                    remove_investment(name, accounts)
                elif how == '4':
                    update_investment(name, accounts)
                elif how == '5':
                    check_balance(name, accounts)
                elif how == '6':
                    time.sleep(0.79)
                    apply_loan(accounts, name)
                elif how == '7':
                    time.sleep(0.79)
                    repay_loan(accounts, name)
                elif how == '8':
                    time.sleep(0.79)
                    view_loan(accounts, name)
                elif how == '9':
                    time.sleep(0.75)
                    amount = float(input("How much money would you like to withdraw? "))
                    withdraw(amount, accounts, name)
                elif how == '10':
                    time.sleep(0.79)
                    check_balance(name, accounts)
                    time.sleep(0.73)
                elif how == '11':
                    time.sleep(0.79)
                    check_personal()
                elif how == '12':
                    time.sleep(0.79)
                    update_personal()
                elif how == '13':
                    time.sleep(0.79)
                    transaction_history(accounts, name)
                elif how == '14':
                    time.sleep(0.79)
                    delete_acc()
                    break
                elif how == '15':
                    update_password()
                elif check_money == '16':
                    time.sleep(0.79)
                    convert_currency(accounts, name)
                elif check_money == '17':
                    time.sleep(0.79)
                    transfer_between_accounts(accounts, name)
                elif how == '18':
                    time.sleep(0.76)
                    print("Alright have a great day. ")
                    time.sleep(0.74)
                    break
                else:
                    print("Invalid Option ")
                    break
        elif accounts[name]["account_type"] == "retirement":
            while True:
                choice = int(input(
                    "Would you like to: 1. View retirement balance, 2. Add funds, 3. Withdraw funds, 4. View personal information, 5. Update personal information, 6. View transaction history, 7. Delete Account, 8. Update password, 9. Apply for a loan, 10. Repay a loan, 11. View loan status, 12. Exit: "))
                if choice == 1:
                    view_retirement_balance(accounts, name)
                elif choice == 2:
                    add_funds_retirement(accounts, name)
                elif choice == 3:
                    withdraw_funds_retirement(accounts, name)
                elif choice == 4:
                    check_personal()
                elif choice == 5:
                    update_personal()
                elif choice == 6:
                    transaction_history(accounts, name)
                elif choice == 7:
                    delete_acc()
                    break
                elif choice == 8:
                    update_password()
                elif choice == 9:
                    time.sleep(0.79)
                    apply_loan(accounts, name)
                elif choice == 10:
                    time.sleep(0.79)
                    repay_loan(accounts, name)
                elif choice == 11:
                    time.sleep(0.79)
                    view_loan(accounts, name)
                elif choice == 12:
                    break
                else:
                    print("Invalid option.")

        else:
            time.sleep(0.73)

            print(
                "How the hell did that happen nah this whole ahh code would fumble blud nah there is no way this would display")

    else:
        print("Incorrect account name or password. Please try again.")
        time.sleep(0.79)
        if name in accounts:
            nah = input("Forgot Password: ").lower()
            if nah in positive_responses:
                forgot_password(accounts)
            elif nah in negative_responses:
                print("Alright havea great day. ")
                return
            else:
                print("Invalid Option. ")
        else:
            return


def main():
    accounts = load_accounts()
    while True:
        choice = int(input("Would you like to: 1. Create a banking account, 2. Sign into a banking account, 3. Forgot Password, 4. Exit: "))
        time.sleep(0.73)
        if choice == 1:
            create_acc(accounts)
        elif choice == 2:
            name = input("Enter account name: ")
            wowie = input("Would you like to see your password as you type or would like it to be hidden? ").lower()
            if wowie in ['see', 'yeah i would like to see', 'seeing']:
                password = input("Enter password: ")
                sign_in(accounts, name, password)
            elif wowie in ['hidden', 'stay hidden']:
                password = custom_getpass("Enter password: ")
                sign_in(accounts, name, password)
            else:
                print("Invalid Option.")
                return
        elif choice == 3:
            forgot_password(accounts)
        elif choice == 4:
            break
        else:
            print("Invalid option.")
            time.sleep(0.73)


if __name__ == "__main__":
    time.sleep(0.73)
    main()
