# MiniBond Issuance with PyTeal and Python SDK
---
To install all required packages: `pip install -r requirements`
A demo script is attached at the bottom of main_publisher.py, to run the demo:
1. submit the publisher and buyer's mnemonic and public address
2. submit the `payment_id` field accepted as payment token, and make sure that your buyer's account is already funded with the asset
3. fetch a recent block number and submit it in the `closure` field.  
