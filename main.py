from hand_tracker import HandTracker

def main():
    """
    Main application entry point for hand tracking with optional WiFi connection
    """
    # Prompt user for connection preference
    while True:
        connect_choice = input("Do you want to connect to WiFi? (Y/N): ").strip().upper()

        if connect_choice == 'Y':
            # Create HandTracker instance with WiFi connection
            tracker = HandTracker(
                host="192.168.4.1",  # WiFi host
                port=80,             # WiFi port
                max_hands=2,         # Maximum hands to track
                detection_confidence=0.7,  # Detection sensitivity
                tracking_confidence=0.5    # Tracking stability
            )
            break
        elif connect_choice == 'N':
            # Create HandTracker instance without WiFi connection
            # Note: You might need to modify the WiFiClientHandler to support a no-connect mode
            try:
                tracker = HandTracker(
                    host=None,        # Disable WiFi connection
                    port=None,        # Disable WiFi connection
                    max_hands=2,      # Maximum hands to track
                    detection_confidence=0.7,  # Detection sensitivity
                    tracking_confidence=0.5    # Tracking stability
                )
            except Exception as e:
                print(f"Error creating tracker: {e}")
                print("Tracker may require a WiFi connection. Consider connecting.")
                continue
            break
        else:
            print("Invalid input. Please enter Y or N.")

    # Start hand tracking
    try:
        tracker.run()
    except Exception as e:
        print(f"An error occurred during hand tracking: {e}")

if __name__ == "__main__":
    main()