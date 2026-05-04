import re
import sys

def validate_ballot(rate_file):
    """
    Validate that a ballot file follows the correct format.
    Returns: (is_valid, error_message)
    """
    try:
        with open(rate_file) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return False, f"Error: File '{rate_file}' not found."
    
    if not lines:
        return False, "Error: File is empty."
    
    # Check for Username line
    first_line = lines[0].strip()
    if not first_line.startswith("Username:"):
        return False, "Error: First line must start with 'Username:'. Example: 'Username: YourName'"
    
    # Check for END line
    if not any(line.strip() == "END" for line in lines):
        return False, "Error: File must end with 'END' on its own line."
    
    in_album = False
    album_count = 0
    song_count = 0
    line_num = 1
    rating_eleven_count = 0
    rating_zero_count = 0
    float_pattern = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)$")
    
    for line in lines:
        line_num += 1
        line = line.rstrip('\n')
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Skip Username line (already checked)
        if stripped.startswith("Username:"):
            continue
        
        # Check for END
        if stripped == "END":
            break
        
        # Check for BONUS TRACKS section
        if stripped.startswith("BONUS TRACKS"):
            in_album = False
            continue
        
        # Check for Album line
        if stripped.startswith("Album:"):
            album_count += 1
            in_album = True
            song_count = 0
            
            # Validate album format: must have "Album:" followed by colon and space
            if ":" not in stripped[6:]:  # After "Album:"
                album_title = stripped[6:].strip()
                if not album_title:
                    return False, f"Error (Line {line_num}): Album line must have a title after 'Album:'. Example: 'Album: Album Title' or 'Album: Album Title with comment'"
            continue
        
        # If we're in an album, validate song lines
        if in_album and not stripped.startswith("Username"):
            song_count += 1
            
            # Check if line has colon
            if ":" not in stripped:
                return False, f"Error (Line {line_num}): Song line must have format 'Song Name: score comment'. Missing colon."
            
            parts = stripped.split(":", 1)
            song_name = parts[0].strip()
            after_colon = parts[1].strip()
            
            if not song_name:
                return False, f"Error (Line {line_num}): Song name cannot be empty. Format: 'Song Name: score comment'"
            
            # If after colon is empty, it's a song without a rating (unrated song) - skip validation
            if not after_colon:
                continue
            
            # Extract the rating (first token after colon)
            tokens = after_colon.split(None, 1)  # Split on first whitespace
            
            if not tokens or not tokens[0]:
                # Empty after colon is allowed (unrated song)
                continue
            
            rating_str = tokens[0]
            
            # Validate rating format (must be valid number with max 1 decimal place)
            if not float_pattern.match(rating_str):
                return False, f"Error (Line {line_num}): Invalid score '{rating_str}'. Scores must be numbers with at most 1 decimal place."
            
            # Check for more than 1 decimal place
            if '.' in rating_str:
                decimal_places = len(rating_str.split('.')[1])
                if decimal_places > 1:
                    return False, f"Error (Line {line_num}): Score '{rating_str}' has {decimal_places} decimal places. Scores must have at most 1 decimal place."
            
            rating = float(rating_str)
            
            # Check if score is valid (typically 0-11)
            if rating < 0 or rating > 11:
                return False, f"Error (Line {line_num}): Score '{rating}' is out of valid range. Scores must be between 0 and 11."
            
            # Track 11 and 0 ratings
            if rating == 11:
                rating_eleven_count += 1
            if rating == 0:
                rating_zero_count += 1
            
            # Check that there's a space after the score if there's a comment
            if len(tokens) > 1 and not after_colon[len(rating_str)].isspace():
                return False, f"Error (Line {line_num}): There must be a space after the score. Format: 'Song Name: score comment' (not 'Song Name: score:comment')"
    
    # Validate counts
    if rating_eleven_count > 1:
        return False, f"Error: Found {rating_eleven_count} songs rated 11. There should be at most 1 song rated 11."
    
    if rating_zero_count > 1:
        return False, f"Error: Found {rating_zero_count} songs rated 0. There should be at most 1 song rated 0."
    
    if album_count == 0:
        return False, "Error: No albums found in ballot. Format: 'Album: Album Name' followed by song ratings."
    
    return True, ""

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python ballot_calculator_album.py <rate file here in .txt format>")
        sys.exit(1)

    rate_file = sys.argv[1]
    
    # Get precision, default to 1 decimal place if not provided
    precision = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    
    # Validate the ballot first
    is_valid, error_msg = validate_ballot(rate_file)
    if not is_valid:
        print(error_msg)
        sys.exit(1)
    
    # If valid, proceed with calculation
    isRating = False
    albumRating = 0.0
    trackCount = 0
    albumAverages = []
    float_pattern = re.compile(r"[-+]?\d*\.\d+|\d+")
    
    # Track special ratings across ALL albums
    all_elevens = None  # Only one 11 allowed
    all_tens = []       # Collect all 10s
    all_zeros = None    # Only one 0 allowed

    with open(rate_file) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("BONUS TRACKS"):
                # Finalize current album if any
                if isRating and trackCount > 0:
                    average = 0.0 if albumRating <= 0 else (albumRating / trackCount)
                    albumAverages.append(average)
                    print(f"||{average:.{precision}f}||")
                elif isRating and trackCount == 0:
                    albumAverages.append(0.0)
                    print(f"||{0.0:.{precision}f}||")
                # Skip all remaining lines until END
                isRating = False
                continue
            if line.startswith("END"):
                if isRating and trackCount > 0:
                    average = 0.0 if albumRating <= 0 else (albumRating / trackCount)
                    albumAverages.append(average)
                    print(f"||{average:.{precision}f}||")
                elif isRating and trackCount == 0:
                    albumAverages.append(0.0)
                    print(f"||{0.0:.{precision}f}||")
                
                # Print special stats at the end
                print()
                if all_elevens:
                    print(f"11: ||{all_elevens}||")
                if all_tens:
                    tens_str = ", ".join(all_tens)
                    print(f"10s: ||{tens_str}||")
                if all_zeros:
                    print(f"0: ||{all_zeros}||")
                break
            if line.startswith("Album:"):
                if isRating and trackCount > 0:
                    average = 0.0 if albumRating <= 0 else (albumRating / trackCount)
                    albumAverages.append(average)
                    print(f"||{average:.{precision}f}||")
                elif isRating and trackCount == 0:
                    albumAverages.append(0.0)
                    print(f"||{0.0:.{precision}f}||")
                # Extract only the album title, ignore anything after the second colon
                album_info = line.split(":", 1)[1].strip()
                # If there's a second colon, take only what's before it
                if ":" in album_info:
                    album_title = album_info.split(":", 1)[0].strip()
                else:
                    album_title = album_info
                print(album_title, end=": ")
                isRating = True
                albumRating = 0.0
                trackCount = 0
                continue
            if isRating and not line.startswith("Album") and not line.startswith("Username"):
                try:
                    # Extract the part after the colon
                    parts = line.split(":", 1)
                    song_name = parts[0].strip()
                    after_colon = parts[1].strip() if len(parts) > 1 else ""
                    # Skip unrated songs (empty after colon)
                    if not after_colon:
                        continue
                    # Find the first float in the string
                    match = float_pattern.search(after_colon)
                    rating = float(match.group()) if match else None
                    if rating is None:
                        continue
                    albumRating += rating
                    trackCount += 1
                    
                    # Track special ratings across all albums
                    if rating == 11:
                        all_elevens = song_name
                    if rating == 10.0 or rating == 10:
                        all_tens.append(song_name)
                    if rating == 0:
                        all_zeros = song_name
                except Exception:
                    print(f"Could not extract rating from line: {line}")

    if albumAverages:
        print("\nAvg: ||{:.{precision}f}||".format(sum(albumAverages) / len(albumAverages), precision=precision))
