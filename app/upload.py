import boto3, botocore
from flask import current_app



s3 = boto3.client(
   "s3",
   aws_access_key_id=current_app.config['S3_KEY_ID'],
   aws_secret_access_key=current_app.config['S3_SECRET_KEY']
)

def delete_file_s3(file_path):
  ## something
  nice = 0


def upload_file_to_s3(file, filename, acl="public-read"):
    try:
        s3.upload_fileobj(
            file,
            current_app.config['S3_BUCKET'],
            file.filename,
            ExtraArgs={
                "ACL": acl
                "ContentType": file.content_type
            }
        )

    except Exception as e:
        print("Something Happened: ", e)
        return e

    return "{}{}".format(current_app.config["S3_LOCATION"], file.filename)