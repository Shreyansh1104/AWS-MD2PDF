
import boto3
import markdown
import os
from urllib.parse import unquote_plus
from fpdf import FPDF
from fpdf.html import HTML2FPDF

s3 = boto3.client("s3")


def lambda_handler(event, context):

    # Get S3 bucket and uploaded file
    record = event["Records"][0]["s3"]

    bucket = record["bucket"]["name"]
    key = unquote_plus(record["object"]["key"])

    # Process only Markdown files in input/
    if not key.startswith("input/") or not key.lower().endswith(".md"):
        return {"status": "ignored"}

    # Download Markdown file
    response = s3.get_object(Bucket=bucket, Key=key)
    md_content = response["Body"].read().decode("utf-8")

    # Convert Markdown to HTML
    html_content = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code"]
    )

    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=11)

    # Parse HTML into PDF
    parser = HTML2FPDF(pdf, image_map={})
    parser.feed(html_content)
    parser.close()

    # Save PDF temporarily
    output_path = "/tmp/output.pdf"
    pdf.output(output_path)

    # Generate output filename
    filename = os.path.basename(key)
    pdf_key = "output/" + os.path.splitext(filename)[0] + ".pdf"

    # Upload PDF to S3
    with open(output_path, "rb") as file:
        s3.put_object(
            Bucket=bucket,
            Key=pdf_key,
            Body=file.read(),
            ContentType="application/pdf"
        )

    return {
        "status": "success",
        "pdf": pdf_key
    }

