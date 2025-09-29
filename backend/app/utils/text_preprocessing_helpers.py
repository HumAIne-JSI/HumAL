import re

# Function to extract the first reply
def extract_first_reply(text):
    """
    This function extracts the first reply from the text.
    It takes a string and returns the first reply.
    The first reply is the text after the first occurrence of the date pattern and 
    before the next occurrence of the date pattern.
    """

    if not text or not isinstance(text, str):
        return None

    # Split the text by the date pattern (assuming format is like "********** 2019-08-05 12:29:10")
    parts = re.split(r'\*+\s*\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', text)
    
    # Return the first part after the first occurrence
    if len(parts) > 1:
        return parts[1].strip()  # Strip to remove extra spaces
    return None

# Function to remove the pattern ": Name (Number) *****"
def remove_name_number_at_beggining(text):
    """
    This function removes the pattern ": Name (Number) *****" from the text.
    """

    if not text or not isinstance(text, str):
        return None

    #cleaned_text = re.sub(r':\s*[A-Za-z]+\s+[A-Za-z]+\s*\(\d+\)\s*\*+', '', text)
    cleaned_text = re.sub(r': .+ \(\d+\) \*+', '', text)
    return cleaned_text.strip()

# Removes the certain pattern from the text
def clean(text):
    """
    This function removes the certain pattern from the text.
    """

    if not text or not isinstance(text, str):
        return None
    
    cleaned_text = re.sub(r'^Dear\s.+,\n?\n?\sBelow\syou\swill\sfind\sthe\sadditional\sform\sinformation\sfor\sthat\srequest\sand\sthe\sinformation\syou\sfilled\sout\.\n-+\n\n-\s', '', text)
    return cleaned_text.strip()

# Function to extract the first 30 characters
def extract_initial_sequence(text):
    """
    This function extracts the first 30 characters from the text.
    """

    if not text or not isinstance(text, str):
        return None
    
    return text[:30]

# Function to categorize text and return a label
def categorize_text(text):
    """
    This function categorizes the text based on the first 30 characters and returns a label.
    """
    # Check if the text is None or empty
    if not text or not isinstance(text, str):
        return (None, 0)
    
    # Category 1 check
    category_1_start = "Need: Extra information needed"
    category_1_start_2 = "Need: Extra information need"
    if text.startswith(category_1_start or category_1_start_2):
        # Extract the text after the sequence and before "\n\n"
        after_sequence = text[len(category_1_start):]
        return (after_sequence.split("\n", 1)[0].strip(), 1)

    # Category 2 check
    category_2_start = "This additional ticke"
    if text.startswith(category_2_start):
        # Return the starting string
        return ("This additional ticket", 2)
    
    # Category 3 check
    category_3_start = "Dear colleague,\n\nPlease note that"
    if text.startswith(category_3_start):
        # Extract the text after the sequence and the text inside the brackets []
        after_sequence = text[len(category_3_start):]
        bracket_content = re.search(r'\[(.*?)\]', after_sequence)
        if bracket_content:
            # Return the concatenated text after the sequence and the bracket content
            return (after_sequence[:bracket_content.end()].strip(), 3)
    
    # Category 4 check
    category_4_start = "Dear colleague,\n\nBecause our service is global"
    if text.startswith(category_4_start):
        # Return the world Italian
        return ("Italian", 4)
    
    # Category 5 (default)
    return ("other", 5)