import os
from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import stripe

from app.Models.StripeModel import StripeModel
from database import AsyncSessionLocal
import app.Utils.crud as crud
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

stripe.api_key = os.getenv('STRIPE_API_KEY')

endpoint_secret = 'whsec_nu25GaHsnPVts5TUOEOReptzASV1mi1i'

print(stripe.api_key)

YOUR_DOMAIN = 'https://rooster.report'

Ember_Price_Id = "price_1Q2EPWAZfjTlvHBok0I7tr1x"
Blaze_Price_Id = "price_1Q2EPzAZfjTlvHBoD9VQ8mQz"
Inferno_Price_Id = "price_1Q2EJRAZfjTlvHBoyeugJqGq"
WildFire_Price_Id = "price_1Q2EMhAZfjTlvHBooIDAfuRC"
Parnter_Plus_Price_Id = "price_1Q2EHmAZfjTlvHBoX4ojWyfW"

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

@router.post('/checkout')
def create_checkout_session(model: StripeModel):
    try:
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # Provide the exact Price ID (for example, pr_1234) of the product you want to sell
                    'price': model.plan_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=YOUR_DOMAIN + '/dashboard/billing?success=true',
            cancel_url=YOUR_DOMAIN + '/dashboard/billingsuccess=false',
        )
    except Exception as e:
        return str(e)
    print(checkout_session.url)
    # return RedirectResponse(url=checkout_session.url, status_code=303)
    return checkout_session.url

@router.post('/webhook')
async def webhook(request: Request, db: Session = Depends(get_db)):
    print("webhook received")
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    if event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        await handle_subscription_created(db, subscription)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        await handle_subscription_updated(db, subscription)

    # elif event['type'] == 'customer.subscription.deleted':
    #     subscription = event['data']['object']
    #     await handle_subscription_deleted(db, subscription)

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        await handle_payment_succeeded(db, invoice)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        await handle_payment_failed(db, invoice)

    else:
        print('Unhandled event type {}'.format(event['type']))

    return JSONResponse(status_code=200, content={"success": True})

async def handle_subscription_created(db, subscription):
    # Example logic for handling subscription created
    customer_id = subscription['customer']
    plan_id = subscription['items']['data'][0]['plan']['id']
    start_date = subscription['start_date']

    # Update your database with subscription details
    print("Subscription created:", subscription['id'])

    # Provision services, send notifications, etc.
    # ...

async def handle_subscription_updated(db, subscription):
    # Example logic for handling subscription updated
    print("Subscription updated:", subscription)

# async def handle_subscription_deleted(db, subscription):
    # await crud.update_usertype(db, user, 0)
    # print("Subscription deleted:", subscription)

async def handle_payment_succeeded(db, invoice):
    sub_id = invoice
    line_item = invoice['lines']['data'][0]
    plan_id = line_item['plan']['id']
    email = invoice['customer_email']
    print("invoice: ", invoice)
    
    user = await crud.get_user_by_email(db, email)
    
    print("user: ", user)
    
    if plan_id == Ember_Price_Id:
        await crud.update_usertype(db, user, 1)
    elif plan_id == Blaze_Price_Id:
        await crud.update_usertype(db, user, 2)
    elif plan_id == Inferno_Price_Id:
        await crud.update_usertype(db, user, 3)
    elif plan_id == WildFire_Price_Id:
        await crud.update_usertype(db, user, 4)
    elif plan_id == Parnter_Plus_Price_Id:
        await crud.update_usertype(db, user, 5)
    
    print("Payment succeeded:", invoice)

async def handle_payment_failed(db, invoice):
    # Example logic for handling payment failed
    print("Payment failed:", invoice)
    