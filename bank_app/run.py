from plaid import Client
from plaid import errors as plaid_errors
from plaid.utils import json

access_token=''
client = Client(client_id='563bf068e7dbd3891f08e57d', secret='')
account_type = 'chase'
username = ''
password = ''


def answer_mfa(data):
    if data['type'] == 'questions':
        # Ask your user for the answer to the question[s].
        # Although questions is a list, there is only ever a
        # single element in this list, at present
        return answer_question([q['question'] for q in data['mfa']])
    elif data['type'] == 'list':
        return answer_list(data['mfa'])
    elif data['type'] == 'selection':
        return answer_selections(data['mfa'])
    else:
        raise Exception('Unknown mfa type from Plaid')

def answer_question(questions):
    # We have magically inferred the answer
    # so we respond immediately
    # In the real world, we would present questions[0]
    # to our user and submit their response
    answer = 'dogs'
    return client.connect_step(account_type, answer)

def answer_list(devices):
    return client.connect_step(account_type, None, options={
        'send_method': {'type': 'phone'}
    })

def answer_selections(selections):
    # We have magically inferred the answers
    # so we respond immediately
    # In the real world, we would present the selection
    # questions and choices to our user and submit their responses
    # in a JSON-encoded array with answers provided
    # in the same order as the given questions
    answer = json.dumps(['Yes', 'No'])
    return client.connect_step(account_type, answer)


try:
    response = client.connect(account_type, {'username': username,'password': password})
except plaid_errors.PlaidError, e:
     pass
else:
    if response.status_code == 200:
        # User connected
        data = json.loads(response.content)
    elif response.status_code == 201:
        # MFA required
        try:
            mfa_response = answer_mfa(json.loads(response.content))
        except plaid_errors.PlaidError, e:
            pass
        else:
            # check for 200 vs 201 responses
            # 201 indicates that additional MFA steps required
            phone_code = raw_input('Enter your ID code from your phone: ')


connected = client.connect_step(account_type, phone_code)

balances = client.balance().json()
response = client.connect_get()
transactions = json.loads(response.content)

