$word = New-Object -ComObject Word.Application
$word.Visible = $false
$doc = $word.Documents.Open("C:\Users\dsant\Desktop\esta\Articulo_CronoGrulla_IEEE.docx")
$pages = $doc.ComputeStatistics([Microsoft.Office.Interop.Word.WdStatistic]::wdStatisticPages)
$doc.Close()
$word.Quit()
Write-Host "Pages: $pages"
