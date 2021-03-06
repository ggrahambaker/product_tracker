import boto3
from flask import current_app





def delete_file_s3(filename):
  s3 = boto3.client(
    "s3",
    aws_access_key_id=current_app.config['S3_KEY_ID'],
    aws_secret_access_key=current_app.config['S3_SECRET_KEY']
  )

  response = s3.delete_objects(
    Bucket=current_app.config['S3_BUCKET'],
    Delete={
        'Objects': [
            {
                'Key': filename
            },
        ]
    }
  )


def upload_file_to_s3(file, filename, acl="public-read"):
  s3 = boto3.client(
    "s3",
    aws_access_key_id=current_app.config['S3_KEY_ID'],
    aws_secret_access_key=current_app.config['S3_SECRET_KEY']
  )


  try:
    s3.upload_fileobj(
          file,
          current_app.config['S3_BUCKET'],
          file.filename,
          ExtraArgs = {
              "ACL": acl,
              "ContentType": file.content_type
          }
    )

  except Exception as e:
      print("Something Happened: ", e)
      return e

  return "{}{}".format(current_app.config["S3_LOCATION"], file.filename)