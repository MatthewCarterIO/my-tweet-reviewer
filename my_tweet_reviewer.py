"""
    File name: my_tweet_reviewer.py
    Author: Matthew Carter
    Date created: 24/04/2019
    Date last modified: 11/08/2019
    Python Version: 3.7.3
"""

import json
import pandas as pd
from os import path
import sys
import webbrowser

TWEETJS_FILENAME = "tweet.js"


# Import the data from tweet.js.
def import_raw_tweets_data(username, gui_compatibility):
    # Check tweet.js file exists in same folder as my_tweet_reviewer program and exit if it isn't found.
    if not path.exists(TWEETJS_FILENAME):
        print("\nERROR: The file tweet.js is not present in the same folder as this program. Please address this and "
              "restart the program.")
        sys.exit()
    with open(TWEETJS_FILENAME, mode='r', encoding="UTF-8") as raw_tweets_data:
        data = raw_tweets_data.read()
        # The data needed from tweet.js is contained within the first "[" and last "]".
        data = data[data.find('['): data.rfind(']')+1]
    tweets_data = json.loads(data)
    # The tweet data comes as a list of dictionaries, each tweet being a dictionaryo of many key-value pairs.
    # For each tweet retrieve just the date of the tweet, tweet ID, tweet text and hashtags.
    tweets_list = []
    for tweet in tweets_data:
        # Date and ID.
        tweet_dict = {"tweet_created": tweet["created_at"], "tweet_id": tweet["id_str"]}
        # Text.
        if gui_compatibility:
            # Remove all special characters such as emojis (can't be displayed in my_tweet_reviewer_GUI.py)
            tweet_dict["tweet_text"] = tweet["full_text"].encode("UTF-8").decode("ascii", errors="ignore")
        else:
            tweet_dict["tweet_text"] = tweet["full_text"]
        # Hashtags. Add hashtags to dictionary only if the tweet contains them.
        tweet_hashtags = []
        for hashtag in tweet["entities"]["hashtags"]:
            tweet_hashtags.append(hashtag["text"])
        if len(tweet_hashtags):
            tweet_dict["tweet_hashtags"] = tweet_hashtags
        # Create complete tweet URL.
        tweet_dict["tweet_url"] = "https://twitter.com/" + username.strip('@') + "/status/" + tweet["id_str"]
        # Append tweet dictionary to tweets list.
        tweets_list.append(tweet_dict)
    # Return list of tweets.
    return tweets_list


# Create new DataFrame of tweets.
def create_tweet_df(original_tweets, gui_compatibility):
    original_tweets_df = pd.DataFrame(original_tweets, columns=["tweet_created", "tweet_id", "tweet_text",
                                                                "tweet_hashtags", "tweet_url"])
    # Convert created_at column of DataFrame to datetime format.
    original_tweets_df["tweet_created"] = pd.to_datetime(original_tweets_df["tweet_created"],
                                                         format='%a %b %d %H:%M:%S %z %Y')
    # Sort DataFrame by date, most recent first.
    original_tweets_df.sort_values(by=["tweet_created"], ascending=False, inplace=True)
    # Extract each hashtag into a column of its own.
    hashtag_df = original_tweets_df["tweet_hashtags"].apply(pd.Series).add_prefix("hashtag_")
    original_tweets_df = pd.concat([original_tweets_df, hashtag_df], axis=1)
    # Drop original hashtags column as it is no longer required.
    original_tweets_df.drop("tweet_hashtags", axis=1, inplace=True)
    # Add a tweet_review_status column to the DataFrame with default "none" values. This column will track the tweets
    # that have been reviewed.
    original_tweets_df["tweet_review_status"] = "none"
    # Add a tweet_url_visited column to the DataFrame with default "no" values. This column will track the tweets that
    # have been viewed in the browser.
    original_tweets_df["tweet_url_visited"] = "no"
    # Add a tweet_deleted column with default "no" values (so CSV can also be used by my_tweet_reviewer_GUI.py).
    if gui_compatibility:
        original_tweets_df["tweet_deleted"] = "no"
    # Return original DataFrame containing tweets.
    return original_tweets_df


# Filter tweets DataFrame.
def filter_tweets(original_df, excluded_hashtags):
    # Get a list containing all hashtag column names in the DataFrame.
    df_col_names = original_df.columns.values.tolist()
    hashtag_col_names = []
    for col_name in df_col_names:
        if "hashtag_" in col_name:
            hashtag_col_names.append(col_name)
    # Create a new DataFrame with rows (tweets) removed if they contain any of the hashtags in the excluded hashtags
    # list.
    filtered_df = original_df.copy()
    for hashtag_col_name in hashtag_col_names:
        # Convert all hashtag columns to lowercase strings.
        filtered_df[hashtag_col_name] = filtered_df[hashtag_col_name].str.lower()
        # Remove rows from DataFrame if there are any hashtags in the exclusion list.
        if len(excluded_hashtags):
            filtered_df = filtered_df[~(filtered_df[hashtag_col_name].isin(excluded_hashtags))]
    # Return the filtered DataFrame.
    return filtered_df


# Iterate through rows of the DataFrame and review each tweet.
def review_tweets(username, excluded_hashtags, saved_filename, gui_compatibility):
    # Load DataFrame.
    df = load_df(username, excluded_hashtags, saved_filename, gui_compatibility)
    # Display number of tweets awaiting review.
    print(count_awaiting_review(df))
    # Iterate through each tweet.
    something_reviewed = False
    quit_reviewing = False
    for tweet_index, tweet_row in df.iterrows():
        # Check if tweet has been reviewed.
        if tweet_row["tweet_review_status"] == "none":
            valid_status = False
            while not valid_status and not quit_reviewing:
                print("\nTweet:")
                print(tweet_row["tweet_text"])
                status_decision = input("Keep (K), delete (D) or pass (P). To quit (Q): ").upper()
                if status_decision in ["K", "D", "P", "Q"]:
                    # Mark tweet row as: K = Keep, D = Delete or P = Pass (e.g. unsure, revisit later) and update
                    # tweet_review_status column in the DataFrame accordingly.
                    valid_status = True
                    if status_decision == "K":
                        something_reviewed = True
                        df.at[tweet_index, "tweet_review_status"] = "keep"
                    elif status_decision == "D":
                        something_reviewed = True
                        df.at[tweet_index, "tweet_review_status"] = "delete"
                    elif status_decision == "P":
                        continue
                    else:
                        # Quit reviewing.
                        quit_reviewing = True
                else:
                    print("\nInvalid review status entered.")
            if quit_reviewing:
                break
    if something_reviewed:
        # One or more tweets reviewed.
        if quit_reviewing:
            # User has chosen to quit.
            print("\nExiting review process.")
        else:
            # User hasn't quit but there are no tweets left to review.
            print("\nNo tweets left to review.")
        # Save DataFrame to CSV.
        save_df_as_csv(df, saved_filename)
    else:
        # No tweets reviewed.
        if quit_reviewing:
            # User has chosen to quit.
            print("\nExiting review process.")
        else:
            # No tweets to review.
            print("\nNo tweets to review.")


# Iterate through rows of the DataFrame, open them in browser for manual deletion and remove from DataFrame if desired.
def delete_tweets(username, excluded_hashtags, saved_filename, gui_compatibility):
    # Load DataFrame.
    df = load_df(username, excluded_hashtags, saved_filename, gui_compatibility)
    # Display number of tweets awaiting deletion.
    print(count_awaiting_deletion(df))
    # Iterate through each tweet.
    something_opened = False
    quit_deleting = False
    for delete_tweet_index, delete_tweet_row in df.iterrows():
        # Check if tweet is marked for deletion in review status and hasn't already been opened in browser.
        if delete_tweet_row["tweet_review_status"] == "delete" and delete_tweet_row["tweet_url_visited"] == "no":
            valid_open = False
            while not valid_open and not quit_deleting:
                open_browser_decision = input("\nOpen next tweet in browser for deletion? (Y/N): ").upper()
                if open_browser_decision in ["Y", "N"]:
                    valid_open = True
                    if open_browser_decision == "Y":
                        something_opened = True
                        print("\nTweet:")
                        print(delete_tweet_row["tweet_text"])
                        # Open tweet in browser.
                        webbrowser.open_new_tab(delete_tweet_row["tweet_url"])
                        # Update the tweet in the DataFrame as having been viewed in the browser.
                        df.at[delete_tweet_index, "tweet_url_visited"] = "yes"
                        # Remove tweet from DataFrame if confirmed deletion occurred.
                        df = remove_tweet(df, delete_tweet_index)
                    else:
                        # Quit deleting.
                        quit_deleting = True
                else:
                    print("\nInvalid choice.")
            if quit_deleting:
                break
    if something_opened:
        # One or more tweets for deletion opened in browser.
        if quit_deleting:
            # User has chosen to quit.
            print("\nExiting delete process.")
        else:
            # User hasn't quit but there are no tweets left to delete.
            print("\nNo tweets left to delete.")
        # Save DataFrame to CSV.
        save_df_as_csv(df, saved_filename)
    else:
        # No tweets for deletion opened in browser.
        if quit_deleting:
            # User has chosen to quit.
            print("\nExiting delete process.")
        else:
            # No tweets to delete.
            print("\nNo tweets to delete.")


# Remove tweet row from DataFrame.
def remove_tweet(df, df_index):
    valid_remove = False
    while not valid_remove:
        remove_decision = input("Has the tweet been deleted? (Y/N): ").upper()
        if remove_decision in ["Y", "N"]:
            valid_remove = True
            if remove_decision == "Y":
                # Remove row.
                df.drop(df_index, inplace=True)
                print("Tweet will be removed from CSV.")
            else:
                # Do not remove row.
                print("Tweet will not been removed from CSV. "
                      "It will only be shown again for review/deletion following a reset.")
                break
        else:
            print("\nInvalid choice.")
    return df


# Save DataFrame as CSV file.
def save_df_as_csv(df, filename):
    valid_save = False
    while not valid_save:
        save_decision = input("\nWould you like to save your progress and quit? "
                              "This will overwrite any existing save file. (Y/N): ").upper()
        if save_decision in ["Y", "N"]:
            valid_save = True
            if save_decision == "Y":
                # Save file.
                if path.exists(filename):
                    print("Overwriting {}.".format(filename))
                else:
                    print("Saving DataFrame to {}.".format(filename))
                df.to_csv(filename, index=None, header=True)
            else:
                # Do not save file.
                print("File not saved.")
        else:
            print("\nInvalid choice.")


# Load existing tweet DataFrame or create a new one.
def load_df(username, excluded_hashtags, saved_filename, gui_compatibility, verbose=True):
    # Check if CSV exists.
    if path.exists(saved_filename):
        # Load existing CSV.
        tweets_df = pd.read_csv(saved_filename, header=0)
        if verbose:
            print("\nLoading existing {}.".format(saved_filename))
    else:
        # Import raw data and create new DataFrame.
        tweets = import_raw_tweets_data(username, gui_compatibility)
        tweets_df = create_tweet_df(tweets, gui_compatibility)
        tweets_df = filter_tweets(tweets_df, excluded_hashtags)
        if verbose:
            print("\nCreating new {}.".format(saved_filename))
    # Number of tweets in csv data.
    if verbose:
        print("Total number of tweets in {}: {}".format(saved_filename, len(tweets_df.index)))
    return tweets_df


# Reset the review status and url visited columns in the DataFrame.
def reset_df(username, excluded_hashtags, saved_filename, gui_compatibility):
    # Load DataFrame.
    df = load_df(username, excluded_hashtags, saved_filename, gui_compatibility)
    # Offer reset.
    valid_reset = False
    while not valid_reset:
        if gui_compatibility:
            reset_question = "\nReset the tweet_review_status, tweet_url_visited and tweet_deleted columns in the " \
                             "data? (Y/N): "
        else:
            reset_question = "\nReset the tweet_review_status and tweet_url_visited columns in the data? (Y/N): "
        reset_decision = input(reset_question).upper()
        if reset_decision in ["Y", "N"]:
            valid_reset = True
            if reset_decision == "Y":
                # Reset columns.
                df["tweet_review_status"] = "none"
                df["tweet_url_visited"] = "no"
                if gui_compatibility:
                    df["tweet_deleted"] = "no"
                print("Columns have been reset.")
                # Save DataFrame to CSV without requiring user confirmation.
                df.to_csv(saved_filename, index=None, header=True)
            else:
                # Cancel reset.
                print("Reset cancelled.")
                break
        else:
            print("\nInvalid choice.")


# Count number of tweets awaiting review.
def count_awaiting_review(df):
    awaiting_review = len(df[df["tweet_review_status"] == "none"])
    return "Awaiting review: {}".format(awaiting_review)


# Count number of tweets awaiting deletion.
def count_awaiting_deletion(df):
    awaiting_deletion = len(df[(df["tweet_review_status"] == "delete") & (df["tweet_url_visited"] == "no")])
    return "Awaiting deletion: {}".format(awaiting_deletion)


# Check for presence of data in the DataFrame.
def data_exists_checker(username, excluded_hashtags, saved_filename, gui_compatibility):
    # Load new or existing DataFrame (verbose=False because not necessary to display anything to user here).
    df = load_df(username, excluded_hashtags, saved_filename, gui_compatibility, verbose=False)
    # Return True if DataFrame contains one or more rows of tweets.
    if len(df.index):
        return True
    else:
        print("\nThere is no tweet data in {0}. Ensure an up to date tweet.js is present "
              "and remove the empty {0} to start again.".format(saved_filename))
        return False


# Run full tweet review and delete process.
def main(username, excluded_hashtags=None, saved_filename=None, gui_compatibility=None):
    # Welcome message.
    print("Welcome to My Tweet Reviewer.")
    # Set defaults if no excluded hashtags list or saved filename is provided.
    if excluded_hashtags is None:
        excluded_hashtags = []
    if saved_filename is None:
        saved_filename = "my_tweet_review.csv"
    if gui_compatibility is None:
        gui_compatibility = False
    # Request user chooses what to do from options Review, Delete, Reset, Quit.
    exit_mytweetreviewer = False
    while not exit_mytweetreviewer:
        while True:
            try:
                choice = int(input("\nWhat would you like to do? Review (1), Delete (2), Reset (3) or Quit (4): "))
                break
            except ValueError:
                print("\nInvalid choice entered. Please choose from options 1-4.")
        if choice in [1, 2, 3, 4]:
            if choice == 1:
                # Review tweets if there is any tweet data present.
                if data_exists_checker(username, excluded_hashtags, saved_filename, gui_compatibility):
                    review_tweets(username, excluded_hashtags, saved_filename, gui_compatibility)
            elif choice == 2:
                # Delete tweets if there is any tweet data present.
                if data_exists_checker(username, excluded_hashtags, saved_filename, gui_compatibility):
                    delete_tweets(username, excluded_hashtags, saved_filename, gui_compatibility)
            elif choice == 3:
                # Reset tweet review status and tweet url columns if there is any tweet data present.
                if data_exists_checker(username, excluded_hashtags, saved_filename, gui_compatibility):
                    reset_df(username, excluded_hashtags, saved_filename, gui_compatibility)
            else:
                # Exit My Tweet Reviewer.
                exit_mytweetreviewer = True
        else:
            print("\nInvalid choice entered. Please choose from options 1-4.")


if __name__ == "__main__":
    # Enter the hashtags included in tweets you wish to remove from review process (without the '#').
    excluded_hashtags_list = ["hashtag1", "hashtag2", "hashtag3"]
    # Enter your Twitter username (including the '@'). The excluded_hashtags and saved_filename parameters are
    # optional.
    main("@yourusername", excluded_hashtags=excluded_hashtags_list, saved_filename="my_tweet_review.csv",
         gui_compatibility=False)
