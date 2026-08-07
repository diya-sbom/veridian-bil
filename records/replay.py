from records.verify_chain import verify_chain

def replay(records):
    passed, message = verify_chain(records)

    if not passed:
        return False, "Replay failed: " + message

    return True, "Replay successful"
