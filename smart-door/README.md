# Smart Door Authenticator Using AWS Kinesis, Rekognition and Lambda 
This folder contains all the code for my second homework project as part of the cloud computing course at columbia.

File Breakdown: 
- Face Streaming Processor: Captures images from the video stream and adds it S3 bucket
- LF1: Takes any event recorded by Kinesis Video Stream (KVS) in Kinesis Data Stream (KDS) and triggers a recognition event that sends a passcode to recognized users. If user is not recognized it allows addition of new user to the system by verification from owner of the smart door. 
- Validate Visitor: Validates the entered passcode to provide access to the virtual door/gate
