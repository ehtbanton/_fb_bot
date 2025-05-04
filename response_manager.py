import excel_manager



def craft_response(message):
    
    response = "You said: " + message # default response

    current_message = message.lower()
    if current_message[:5] == "hello":
        response = "Hello! I am Nancy-Bot. Everything ok?"

    elif current_message[:5] == "thank":
        response = "No problem bro"
    
    elif current_message[:5] == "book ":
        # e.g. "book CB1 05-05-2025 DPT"
        parts = current_message.split(" ")
        voice_part = parts[1]  # e.g. "CB1"
        print("Voice part: " , voice_part)
        date_str = parts[2]    # e.g. "05-05-2025"
        print("Date: " , date_str)
        dep_initials = parts[3] # e.g. "DPT"
        print("Dep initials: " , dep_initials)


        excel_manager.update_sheet_range()
        success = excel_manager.update_cell(date_str, voice_part, dep_initials, "yellow")
        if not success:
            response = "Sorry, I can't do that."
            return response
        response = "Thanks - I've booked in " + dep_initials + " on " + date_str + " for " + voice_part + "."
    
    elif current_message[:7] == "cancel ":
        # e.g. "cancel CB1 05-05-2025
        parts = current_message.split(" ")
        voice_part = parts[1]  # e.g. "CB1"
        print("Voice part: " , voice_part)
        date_str = parts[2]    # e.g. "05-05-2025"
        print("Date: " , date_str)

        excel_manager.update_sheet_range()
        success = excel_manager.update_cell(date_str, voice_part, "", "green")

        if not success:
            response = "Sorry, I can't do that."
            return response
        response = "Ok, I've cancelled your booking for " + voice_part + " on " + date_str + "."

    return response