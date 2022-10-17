import json
import psycopg2

from kafka import KafkaConsumer

# Connecting to Kafka Server
consumer = KafkaConsumer(
    'siemensserver1.siemens.asset',
    bootstrap_servers=['kafka:9092'],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='1'
)

# Compares the values of every payload element and returns a list with every element that changed
def getChangedTags(payload_before, payload_after):
    tags = []
    for tag in payload_before:
        tags.append(tag)

    changedTags = []
    for i in range(len(tags)):
        if str(payload_before[tags[i]]) != str(payload_after[tags[i]]):
            changedTags.append(tags[i])

    return changedTags

# Connects to Database and executes Update query for every changed element
def sendChangesToDatabase(changedTags, payload_after, primaryKey):
    try:
        connection = psycopg2.connect(user="postgres",
                                  password="password",
                                  host="localhost",
                                  port="5433",
                                  database="postgres")
        cursor = connection.cursor()

        sql_update_query = "Update siemens.asset set {} = {} where {} = {}"
        key = list(primaryKey.keys())[0]
        for i in range(len(changedTags)):
            cursor.execute(sql_update_query.format(changedTags[i], payload_after[changedTags[i]], key, primaryKey[key]))
            connection.commit()
            count = cursor.rowcount
            print(count, "Record Updated successfully ")
            
    except (Exception, psycopg2.Error) as error:
        print("Error in update operation", error)

    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

# Debugging
if(consumer.bootstrap_connected()):
    print('Successfully connected')
    print(consumer.subscription())

# Loop, waiting for new Kafka Message
for message in consumer:
    print(message.key)
    payload = json.loads(message.value)["payload"]
    payload_before = payload["before"]
    payload_after = payload["after"]
    print('Message Received: {}'.format(message.value))
    print('Payload Before:')
    print(payload_before)
    print('Payload After:')
    print(payload_after)
    print()
    # If something changed
    if payload_before is not None:
        # Get the Tags that have changed values
        changedTags = getChangedTags(payload_before, payload_after)
        # Print Changed Tags
        for i in range(len(changedTags)):
            print(str(changedTags[i]) + ' Changed.')
        print()
        # Send Changed to Database, 3rd Parameter is the primary key of the received Message
        sendChangesToDatabase(changedTags, payload_after, json.loads(message.key)["payload"])
    