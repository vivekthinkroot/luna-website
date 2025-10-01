// app/routes/pdf.ts
import type { LoaderFunction } from "@remix-run/node";
import { PDFDocument, rgb, StandardFonts } from "pdf-lib";
import fetch from "node-fetch";

type RazorpayPayment = {
  id: string;
  entity: string;
  amount?: number;
  currency?: string;
  status?: string;
  method?: string;
  email?: string;
  contact?: string;
  created_at?: number;
};
export const loader: LoaderFunction = async ({ request }) => {
  try {
    const url = new URL(request.url);
    const paymentId = url.searchParams.get("paymentId");
    if (!paymentId) {
      return new Response(JSON.stringify({ error: "Missing paymentId" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      });
    }

    const razorpayKey = "rzp_test_REL5i4sFob9AwE"; // your key
    const razorpaySecret = "zPot7U8zDeWgpgiMlY03AHdi"; // your secret

    // Fetch payment details
    let payment: RazorpayPayment = { id: paymentId, entity: "payment" };
    try {
      const res = await fetch(
        `https://api.razorpay.com/v1/payments/${paymentId}`,
        {
          headers: {
            Authorization: `Basic ${Buffer.from(
              `${razorpayKey}:${razorpaySecret}`
            ).toString("base64")}`,
          },
        }
      );

      const data = (await res.json()) as RazorpayPayment;

      if (res.ok && data) {
        payment = data;
      } else {
        payment.status = "Failed to fetch payment";
        payment.method = JSON.stringify(data);
      }
    } catch (err: any) {
      payment.status = "Error fetching payment";
      payment.method = err.message;
    }

    // Create PDF
    const pdfDoc = await PDFDocument.create();
    const page = pdfDoc.addPage([600, 700]);
    const { width, height } = page.getSize();

    const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const helveticaBoldFont = await pdfDoc.embedFont(
      StandardFonts.HelveticaBold
    );

    // Header
    page.drawRectangle({
      x: 0,
      y: height - 100,
      width,
      height: 100,
      color: rgb(0.95, 0.85, 0.2), // golden header
    });

    // Function to draw your SVG star
    
    // Draw star and heading // yellow star
    page.drawText("AstroVision", {
      x: 80,
      y: height - 70,
      size: 30,
      font: helveticaBoldFont,
      color: rgb(0.1, 0.1, 0.1),
    });

    // Receipt title
    page.drawText("Payment Receipt", {
      x: 50,
      y: height - 140,
      size: 24,
      font: helveticaBoldFont,
    });

    // Payment info box
    const boxX = 50;
    let boxY = height - 200;
    const boxWidth = 500;
    const boxHeight = 200;

    page.drawRectangle({
      x: boxX,
      y: boxY - boxHeight,
      width: boxWidth,
      height: boxHeight,
      borderColor: rgb(0.2, 0.2, 0.2),
      borderWidth: 1.5,
      color: rgb(0.98, 0.98, 0.98),
    });

    const lineGap = 25;
    let textY = boxY - 40;

    page.drawText(`Payment ID: ${payment.id || "N/A"}`, {
      x: boxX + 20,
      y: textY,
      size: 16,
      font: helveticaFont,
    });

    textY -= lineGap;
    page.drawText(
      `Amount Paid: INR ${payment.amount ? payment.amount / 100 : "N/A"}`,
      {
        x: boxX + 20,
        y: textY,
        size: 16,
        font: helveticaFont,
        color: rgb(0.8, 0.5, 0.1),
      }
    );

    textY -= lineGap;
    page.drawText(`Status: ${payment.status || "N/A"}`, {
      x: boxX + 20,
      y: textY,
      size: 16,
      font: helveticaFont,
      color:
        payment.status?.toLowerCase() === "captured"
          ? rgb(0, 0.6, 0)
          : rgb(0.8, 0, 0),
    });

    textY -= lineGap;
    page.drawText(`Method: ${payment.method || "N/A"}`, {
      x: boxX + 20,
      y: textY,
      size: 16,
      font: helveticaFont,
    });

    textY -= lineGap;
    page.drawText(`Contact: ${payment.contact || "N/A"}`, {
      x: boxX + 20,
      y: textY,
      size: 16,
      font: helveticaFont,
    });

    textY -= lineGap;
    page.drawText(`Email: ${payment.email || "N/A"}`, {
      x: boxX + 20,
      y: textY,
      size: 16,
      font: helveticaFont,
    });

    textY -= lineGap;
    page.drawText(
      `Date: ${
        payment.created_at
          ? new Date(payment.created_at * 1000).toLocaleString()
          : "N/A"
      }`,
      { x: boxX + 20, y: textY, size: 16, font: helveticaFont }
    );

    // Tick icon for paid status
    if (payment.status?.toLowerCase() === "captured") {
      page.drawText("Paid Successfully", {
        x: boxX + 350,
        y: boxY - 40,
        size: 14,
        font: helveticaBoldFont,
        color: rgb(0, 0.6, 0),
      });
    }

    // Footer
    page.drawText("Thank you for choosing AstroVision!", {
      x: 50,
      y: 50,
      size: 14,
      font: helveticaFont,
      color: rgb(0.3, 0.3, 0.3),
    });

    const pdfBytes = await pdfDoc.save();

    return new Response(Buffer.from(pdfBytes), {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="payment_receipt_${paymentId}.pdf"`,
      },
    });
  } catch (err: any) {
    console.error("Unexpected error:", err);

    const pdfDoc = await PDFDocument.create();
    const page = pdfDoc.addPage([600, 400]);
    const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
    page.drawText("Failed to generate PDF", { x: 50, y: 350, size: 24, font });
    page.drawText(`Error: ${err.message}`, { x: 50, y: 300, size: 16, font });

    const pdfBytes = await pdfDoc.save();

    return new Response(Buffer.from(pdfBytes), {
      status: 500,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="payment_error.pdf"`,
      },
    });
  }
};
