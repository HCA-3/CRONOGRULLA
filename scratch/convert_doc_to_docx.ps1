$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("C:\Users\dsant\Desktop\esta\PLANTILLA-IEEE_2026.doc")
# Save as DOCX (wdFormatXMLDocument = 16)
$doc.SaveAs("C:\Users\dsant\Desktop\esta\PLANTILLA-IEEE_2026.docx", 16)
$doc.Close()
$word.Quit()
Write-Host "Success! Plantilla converted to DOCX."
