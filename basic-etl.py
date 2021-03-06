# ETL JSON files into CSV and PostgreSQL

# run once
#   pip install csvkit
#   initdb dataaoc
#   postgres -D dataaoc/
#   createdb tweetreplies

import os, csv, json

tweets = os.listdir('./all_tweets')


with open('./all_tweets/origin_tweets.csv', 'w') as csv1:
    originTweets = csv.writer(csv1)
    originTweets.writerow(['tweetid','timestamp','printname','screenname','verified','body','quotescreenname','quotetext','likes','retweets'])

    with open('./all_tweets/replies.csv', 'w') as csv2:
        replyTweets = csv.writer(csv2)
        replyTweets.writerow(['tweetid','convoid','timestamp','printname','screenname','verified','mentions','cards','body','lang','links','likes','retweets'])

        seenOrigins = {}
        seenReplies = {}

        for tweet in tweets:
            if '.json' in tweet:
                d = json.loads(open('./all_tweets/' + tweet, 'r').read())
                origin = d['origin']
                tweetid = origin[0]
                if tweetid not in seenOrigins:
                    originTweets.writerow(origin)
                    seenOrigins[tweetid] = True

                replies = d['replies']
                for reply in replies:
                    tweetid = reply[0]
                    if tweetid not in seenReplies:
                        replyTweets.writerow(reply)
                        seenReplies[tweetid] = True


os.system('csvsql --insert --overwrite --db postgresql:///tweetreplies ./all_tweets/origin_tweets.csv')
os.system('csvsql --insert --overwrite --db postgresql:///tweetreplies ./all_tweets/replies.csv')

# psql tweetreplies
"""
DROP TABLE IF EXISTS origins;
DROP TABLE IF EXISTS combined;
CREATE TABLE origins AS (
    SELECT tweetid AS originid, timestamp AS origintime, printname AS originname,
    screenname AS originsn, verified AS originverified, body AS originbody,
    quotescreenname, quotetext, likes AS originlikes, retweets AS originretweets
    FROM origin_tweets
);
CREATE TABLE combined AS (
    SELECT * FROM replies
    JOIN origins ON replies.convoid = origins.originid
);
"""

"""
APPROACH B

SELECT COUNT(*), screenname FROM replies
    WHERE LOWER(screenname) LIKE '%trump%' OR LOWER(printname) LIKE '%trump%'
        OR LOWER(screenname) LIKE '%maga%' OR LOWER(printname) LIKE '%maga%'
        OR LOWER(screenname) LIKE '%anon%' OR LOWER(printname) LIKE '%anon%'
        OR LOWER(screenname) LIKE '%nationalis%' OR LOWER(printname) LIKE '%nationalis%'
        OR screenname ~ '\d\d\d$' OR printname ~ '\d\d\d\d\d$'
    GROUP BY screenname
    ORDER BY COUNT(*) DESC;

WITH funusers AS (
    SELECT COUNT(*) AS count, screenname FROM replies
        WHERE LOWER(screenname) LIKE '%trump%' OR LOWER(printname) LIKE '%trump%'
            OR LOWER(screenname) LIKE '%maga%' OR LOWER(printname) LIKE '%maga%'
            OR LOWER(screenname) LIKE '%anon%' OR LOWER(printname) LIKE '%anon%'
            OR LOWER(screenname) LIKE '%nationalis%' OR LOWER(printname) LIKE '%nationalis%'
            OR screenname ~ '\d\d\d$' OR printname ~ '\d\d\d\d\d$'
        GROUP BY screenname
        ORDER BY COUNT(*)
)
SELECT AVG(count) FROM funusers;

SELECT COUNT(*) FROM replies
    WHERE LOWER(screenname) LIKE '%trump%' OR LOWER(printname) LIKE '%trump%'
        OR LOWER(screenname) LIKE '%maga%' OR LOWER(printname) LIKE '%maga%'
        OR LOWER(screenname) LIKE '%anon%' OR LOWER(printname) LIKE '%anon%'
        OR LOWER(screenname) LIKE '%nationalis%' OR LOWER(printname) LIKE '%nationalis%'
        OR screenname ~ '\d\d\d$' OR printname ~ '\d\d\d\d\d$';

DROP TABLE IF EXISTS aset;
CREATE TABLE aset AS (SELECT * FROM combined);
ALTER TABLE aset ADD COLUMN skeptical_name BOOLEAN;
UPDATE aset SET skeptical_name = FALSE WHERE 1 = 1;
UPDATE aset SET skeptical_name = TRUE WHERE
        LOWER(screenname) LIKE '%trump%' OR LOWER(printname) LIKE '%trump%'
        OR LOWER(screenname) LIKE '%maga%' OR LOWER(printname) LIKE '%maga%'
        OR LOWER(screenname) LIKE '%anon%' OR LOWER(printname) LIKE '%anon%'
        OR LOWER(screenname) LIKE '%nationalis%' OR LOWER(printname) LIKE '%nationalis%'
        OR screenname ~ '\d\d\d$' OR printname ~ '\d\d\d\d\d$';

DROP TABLE IF EXISTS aset_automl;
CREATE TABLE aset_automl AS (
    SELECT REPLACE(CONCAT(CONCAT(originbody, ' || '), body), E'\n', ''), skeptical_name
    FROM aset
);

DROP TABLE IF EXISTS aset_automl_2;
CREATE TABLE aset_automl_2 AS (
    SELECT REPLACE(body, E'\n', ''), skeptical_name
    FROM aset
);

DROP TABLE IF EXISTS aset_azure;
CREATE TABLE aset_azure AS (
    SELECT
        skeptical_name, timestamp, verified, mentions, cards, body, lang, links, likes, retweets, origintime, originname, originsn, originverified, originbody, quotescreenname, quotetext, originlikes, originretweets,
        REPLACE(REPLACE(REPLACE(REPLACE(LOWER(printname), 'trump', ''), 'maga', ''), 'anon', ''), 'nationalis', '') AS printname,
        REPLACE(REPLACE(REPLACE(REPLACE(LOWER(screenname), 'trump', ''), 'maga', ''), 'anon', ''), 'nationalis', '') AS screenname
    FROM aset
    WHERE skeptical_name
) UNION (
    SELECT
        skeptical_name, timestamp, verified, mentions, cards, body, lang, links, likes, retweets, origintime, originname, originsn, originverified, originbody, quotescreenname, quotetext, originlikes, originretweets,
        REPLACE(REPLACE(REPLACE(REPLACE(LOWER(printname), 'trump', ''), 'maga', ''), 'anon', ''), 'nationalis', '') AS printname,
        REPLACE(REPLACE(REPLACE(REPLACE(LOWER(screenname), 'trump', ''), 'maga', ''), 'anon', ''), 'nationalis', '') AS screenname
    FROM aset
    WHERE skeptical_name = FALSE
    LIMIT 19500
);
"""

# sql2csv --no-header-row --db postgres:///tweetreplies --query 'SELECT * FROM aset_automl LIMIT 99000' > all_tweets/aset_automl.csv
# sql2csv --no-header-row --db postgres:///tweetreplies --query 'SELECT * FROM aset_automl_2 WHERE LENGTH(TRIM(replace)) > 0 LIMIT 99000' > all_tweets/aset_automl_2.csv

# sql2csv --db postgres:///tweetreplies --query 'SELECT * FROM aset_azure' > all_tweets/aset_azure.csv
