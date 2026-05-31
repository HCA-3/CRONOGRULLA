$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("C:\Users\dsant\Desktop\esta\PLANTILLA-IEEE_2026.doc")
$text = $doc.Content.Text
$text | Out-File "c:\Users\dsant\Desktop\U CATOLICA\ING INDUSTRIAL\SEMESTRES INDUSTRIAL\segundo semestre\ingenieria de metodos\Corte 1\ingenieria de metodos\scratch\PLANTILLA-IEEE_2026.txt" -Encoding utf8
$doc.Close()
$word.Quit()
Write-Host "Success!"
