set CATEGORIZE_FILE="C:\Users\osama\categorize.cfg"
set CATEGORY="Graph"
set FILTER="\$sampleage <= 2922:00" 

arbtt-stats --categorizefile=%CATEGORIZE_FILE% --for-each=day --output-format=CSV --category=%CATEGORY% --min-percentage=0.1 > daily.csv

arbtt-stats --categorizefile=%CATEGORIZE_FILE% --for-each=minute --output-format=CSV --category=%CATEGORY% --min-percentage=0.1 > minute.csv

