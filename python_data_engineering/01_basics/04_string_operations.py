"""Common string operations used in data engineering."""


def clean_column_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def mask_email(email: str) -> str:
    user, _, domain = email.partition("@")
    if len(user) <= 2:
        return "*" * len(user) + "@" + domain
    return user[0] + "*" * (len(user) - 2) + user[-1] + "@" + domain


def is_valid_phone(phone: str) -> bool:
    digits = "".join(ch for ch in phone if ch.isdigit())
    return 10 <= len(digits) <= 13


def main() -> None:
    print(clean_column_name("  Customer Name  "))
    print(mask_email("sharath@example.com"))
    print(is_valid_phone("+91-9876543210"))


if __name__ == "__main__":
    main()
