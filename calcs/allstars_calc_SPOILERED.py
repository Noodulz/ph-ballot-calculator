import re
import sys

if len(sys.argv) < 2:
    print("Usage: python all_stars_average.py <rate file here in .txt format>")
    sys.exit(1)

rate_file = sys.argv[1]

# Get precision, default to 1 decimal place if not provided
precision = int(sys.argv[2]) if len(sys.argv) > 2 else 1

# Read the file
with open(rate_file, 'r') as f:
    content = f.read()

# Extract all ratings (numbers that appear after song names, not in "Rate:" lines)
lines = content.split('\n')
ratings = []
rating_11 = []
rating_10 = []
rating_0 = []

for line in lines:
    # Skip lines that are rate category titles
    if line.strip().startswith('Rate:'):
        continue
    
    # Look for song entries (contain a dash and a number)
    if ' - ' in line:
        # Extract the rating number from the line
        match = re.search(r':\s*([\d.]+)', line)
        if match:
            score = float(match.group(1))
            ratings.append(score)
            
            # Extract song name (everything before the colon)
            song_match = re.search(r'-\s*(.+?):', line)
            if song_match:
                song_name = song_match.group(1).strip()
                
                if score == 11:
                    rating_11.append(song_name)
                elif score == 10:
                    rating_10.append(song_name)
                elif score == 0:
                    rating_0.append(song_name)

# Calculate average
average = sum(ratings) / len(ratings) if ratings else 0

# Format output
print(f"11: ||{', '.join(rating_11) if rating_11 else 'None'}||")
print(f"10s: ||{', '.join(rating_10) if rating_10 else 'None'}||")
print(f"0: ||{', '.join(rating_0) if rating_0 else 'None'}||")
print(f"\nAvg: ||{average:.{precision}f}||")