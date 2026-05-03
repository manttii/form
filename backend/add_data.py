import sys
import os

# Add the current directory to path so we can import data_pool
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import data_pool

def main():
    print("--- Form Automator Data Manager ---")
    print("1. Add Names (Auto-splits First/Last)")
    print("2. Add Other Data (Emails, Cities, etc.)")
    print("3. Exit")
    
    choice = input("\nSelect option: ")
    
    if choice == '1':
        name = input("Enter full name (e.g. John Doe): ")
        if name:
            res = data_pool.smart_add_name(name)
            print(f"Success! Added First: '{res['first']}', Last: '{res['last']}' and Full: '{name}'")
    
    elif choice == '2':
        categories = [
            "random_emails", "random_phone", "random_ages", "random_sentences",
            "random_words", "random_address", "random_company", "random_city",
            "random_country", "random_job", "random_username", "random_number"
        ]
        print("\nAvailable Categories:")
        for i, cat in enumerate(categories, 1):
            print(f"{i}. {cat.replace('random_', '')}")
            
        cat_idx = int(input("\nSelect category number: ")) - 1
        if 0 <= cat_idx < len(categories):
            cat = categories[cat_idx]
            val = input(f"Enter value for {cat}: ")
            if val:
                data_pool.save_to_pool(cat, [val])
                print(f"Added '{val}' to {cat}.json")
    
    else:
        print("Exiting.")

if __name__ == "__main__":
    main()
