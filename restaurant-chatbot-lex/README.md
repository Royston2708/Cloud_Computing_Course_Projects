# Restaurant Reservation Chatbot
This section contains the code for the restaurant chatbot concierge project that can make reservations at a restaurant in NYC using preferences such as cuisine, number of individuals, time of reservation, etc. 

File Breakdown: 
- LF0 : Function connecting the front end to API Gateway and Amazon Lex
- LF1 : Function that gets the response from Amazon Lex and adds restaurant suggestion to SQS queue if all slots have been filled 
- LF2 : Function that polls for entries in SQS Queue and sends message to user after querying elasticsearch index.
