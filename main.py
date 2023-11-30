
import json
import os
import subprocess
import shlex
import boto3

S3_BUCKET = "<Enter Bucket name here>"
SIGNED_URL_TIMEOUT = 600

def lambda_handler(event, context):

    s3_source_bucket = event['Records'][0]['s3']['bucket']['name']
    s3_source_key = event['Records'][0]['s3']['object']['key']

    s3_source_basename = os.path.splitext(os.path.basename(s3_source_key))[0]
    s3_destination_filename_gif = "thumb_" + s3_source_basename + ".gif"
    s3_destination_filename_thumbnail = "vidthumb_" + s3_source_basename + ".png"

    s3_client = boto3.client('s3')
    s3_source_signed_url = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': s3_source_bucket, 'Key': s3_source_key},
        ExpiresIn=SIGNED_URL_TIMEOUT)
    if os.path.exists("/tmp/output.gif"):
        os.remove("/tmp/output.gif")
    if os.path.exists("/tmp/compressed.gif"):
        os.remove("/tmp/compressed.gif")
    if os.path.exists("/tmp/thumbnail.png"):
        os.remove("/tmp/thumbnail.png")
    #################################
    # Generate Thumbnail
    #################################
    ffmpeg_cmd = "ffmpeg -ss 00:00:02 -i \"" + s3_source_signed_url + "\" -filter:v \"scale='min(700,iw)':-1\" -frames:v 1 /tmp/thumbnail.png"
    command1 = shlex.split(ffmpeg_cmd)
    p1 = subprocess.call(ffmpeg_cmd, shell=True)
    # Upload Thumbnail to dstination
    s3_client.upload_file("/tmp/thumbnail.png", Bucket=S3_BUCKET, Key="images/thumbnail/" + s3_destination_filename_thumbnail)
    #################################
    # End Generate Thumbnail
    #################################
    
    
    ##################################
    # Generate GIF
    ##################################
    ffmpeg_cmd = "ffmpeg -t 60 -i \"" + s3_source_signed_url + "\" -filter_complex \"fps=10,scale=450:-1[s]; [s]split[a][b]; [a]palettegen[palette]; [b][palette]paletteuse\" /tmp/output.gif"
    command1 = shlex.split(ffmpeg_cmd)
    p1 = subprocess.call(ffmpeg_cmd, shell=True)
    # Compress GIF
    gifsicle_cmd = "gifsicle -O3 --lossy=80 /tmp/output.gif -o /tmp/compressed.gif"
    command1 = shlex.split(gifsicle_cmd)
    p1 = subprocess.call(gifsicle_cmd, shell=True)
    # Upload GIF to destination
    s3_client.upload_file("/tmp/compressed.gif", Bucket=S3_BUCKET, Key="images/thumbnail/" + s3_destination_filename_gif)
    ####################################
    # END Generate GIF and Compress GIF
    ####################################
    
    return {
        'statusCode': 200,
        'body': json.dumps('Processing complete successfully')
    }
