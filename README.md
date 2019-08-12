# my-tweet-reviewer

## Introduction

My Tweet Reviewer allows you to review each of the tweets in your downloaded Twitter data and to conveniently open those you choose to delete in your internet browser for quick removal.

This is not designed to be a bulk tweet review or delete program; it is intended to offer control for a more considered approach. To support this, the review process can be done offline and progress can be saved at any point and resumed at a later time.

## Installation

### Prerequisites

* [python 3.7.3](https://www.python.org/) 
* [pandas 0.25.0](https://pandas.pydata.org/index.html)
* tweet.js

### Getting Started

1. Download or update Python and the pandas library as required. 
2. Request and download the Twitter data from the account you wish to review.
3. Copy the `tweet.js` file from your downloaded data into the same folder as the `my_tweet_reviewer.py` file.
4. Open `my_tweet_reviewer.py` in your desired environment.

## Usage

A CSV file is created from `tweet.js` and is updated as you progress through the review and delete processes. The columns in the CSV file are as follows:

- `tweet_created` - Date the tweet was created.
- `tweet_id` - Unique ID of the tweet.
- `tweet_text` - Text of the tweet.
- `tweet_url` - Web address for the tweet.
- `hashtag_X` - One column allocated to each of the hashtags in the tweet.
- `tweet_review_status` - The review status you assign to the tweet during the review process.
- `tweet_url_visited` - Whether the tweet has been opened in the browser during the delete process.
- `tweet_deleted` - Whether the tweet has been deleted during the delete process.

During the review process, tweets are marked to keep or delete. Any tweets marked for deletion can then be automatically opened in your internet browser one at a time during the delete process, allowing you to quickly remove them without needing to scroll through all of your tweets to search for them. It is not necessary to review all tweets before deleting, tweets can be deleted at any time.

This program can largely be used offline, but to delete tweets you need to be online and logged into your Twitter account (to access delete option).

### Initial Setup

Prior to running the program locate and complete the section of code shown below:

```python
if __name__ == "__main__":
    excluded_hashtags_list = ["hashtag1", "hashtag2", "hashtag3"]
    main("@yourusername", excluded_hashtags=excluded_hashtags_list, saved_filename="my_tweet_review.csv", gui_compatibility=False)
```

- `username` (Required) - Your Twitter username including '@' symbol.
- `excluded_hashtags` (Optional) - A list of hashtags included in tweets you do not want/need to review (without the '#' character).
- `saved_filename` (Optional) - Name of the new CSV save file to create if one doesn't exist, or that currently exists and you wish to continue using.
- `gui_compatibility` (Optional) - Enable compatibility with My Tweet Reviewer GUI. `True` value enables compatibility with the GUI version. The `tweet_deleted` column is only used in the CSV save file of My Tweet Reviewer GUI, but can be added when creating the CSV in this program so that both versions can be used interchangeably with the same save file. Special characters such as emojis will also be removed from tweets as they are in the GUI version (tkinter package unable to display some characters). 

Starting the program presents four options: `Review (1)`, `Delete (2)`, `Reset (3)` or `Quit (4)` which are elaborated on below. The characters in brackets correspond to the keyboard numbers/letters for each selection (letter case is not important).

### Review

Starts or resumes the review process by loading the contents of the CSV into a pandas DataFrame. The `tweet_review_status` column in the DataFrame will be updated during the review process. The DataFrame will be used to overwrite the CSV file if a save is performed.

1. The next tweet for review is shown if there is one. For each tweet you have the option to select a review status (by default it is `None`) or to quit. The choices are:
- `Keep (K)` - Tweet will be kept in the CSV and will not shown again for review.
- `Delete (D)` - Tweet will be marked for deletion in the CSV, awaiting the start of the delete process.
- `Pass (P)` - Move onto the next tweet for review if there is one. Passed tweets are shown again when the review process is restarted.
- `Quit (Q)` - Stop the review process and save your progress to the CSV if necessary. 
2. If you selected a review status in step one, the next tweet for review will be shown if there is one. If you quit and at least one review status has been changed, you are given the opportunity to save your progress to the CSV:
- `Y` - Save DataFrame to the CSV, overwriting any existing data.
- `N` - Exit without saving. Any unsaved progress will be lost and tweets will have to be reviewed again.

If there are no tweets to review, a message will be shown and the process is the same as if you'd quit. 

### Delete

Starts or resumes the delete process by loading the contents of the CSV into a pandas DataFrame. The `tweet_url_visited` and `tweet_deleted` (if present) columns in the DataFrame will be updated during the delete process. The DataFrame will be used to overwrite the CSV file if a save is performed.

1. Open the next tweet marked for deletion in your internet browser if there is one:
- `Y` - Opens the tweet.
- `N` - Does not open the tweet and stops the delete process. Go to step four.
2. Once opened in the browser, delete the tweet as you normally would.
3. Return to the program and confirm whether the tweet was deleted. Take care with this step as data may be removed from your CSV based on your choice:
- `Yes` - Tweet will be removed from the CSV. 
- `No` - Tweet will remain in the CSV but will not be shown again for review or deletion until a reset or a manual edit of the CSV file has been done. 
4. If you completed step three, you can open the next tweet for deletion if there is one. If you exit the delete process and at least one tweet has been opened in your browser, you are given the opportunity to save your progress to the CSV:
- `Y` - Save DataFrame to the CSV, overwriting any existing data.
- `N` - Exit without saving. Any unsaved progress will be lost regardless of whether the tweet has actually been deleted.

If there are no tweets to delete, a message will be shown and the process is the same as if you'd declined to open a tweet. 

### Reset

Resets the values in the `tweet_review_status`, `tweet_url_visited` and `tweet_deleted` (if present) columns for all tweets in the CSV file, allowing the review and delete processes to be restarted.
- `Y` - Reset and automatically save DataFrame to the CSV, overwriting any existing data.
- `N` - Cancel reset.

### Quit

Exits the program without saving.

## Testing

The program was last tested with the `tweet.js` format as of 31/07/2019. 

## Author

**Matthew Carter** - [MatthewCarterIO](https://github.com/MatthewCarterIO)