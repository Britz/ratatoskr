FROM mcr.microsoft.com/devcontainers/python:1-3.12

ARG USERNAME=vscode

RUN mkdir -p /usr/share/keyrings && \
    curl -fsSL https://dl.yarnpkg.com/debian/pubkey.gpg | gpg --batch --yes --dearmor -o /usr/share/keyrings/yarn-archive-keyring.gpg

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-deu \
        tesseract-ocr-eng \
        tesseract-ocr-dan \
        tesseract-ocr-swe \
        tesseract-ocr-nor \
        tesseract-ocr-fra \
        tesseract-ocr-lat \
        qpdf \
        ocrmypdf \
        imagemagick \
        img2pdf \
        jpegoptim \
        optipng \
        libimage-exiftool-perl && \
    rm -rf /var/lib/apt/lists/*

RUN --mount=type=bind,source=.,target=/build_ctx \
    USERNAME_FINAL="${USERNAME:-vscode}"; \
    TARGET_UID=$(cat /build_ctx/.local_uid 2>/dev/null | tr -dc '0-9'); \
    TARGET_GID=$(cat /build_ctx/.local_gid 2>/dev/null | tr -dc '0-9'); \
    TARGET_UID=${TARGET_UID:-1000}; \
    TARGET_GID=${TARGET_GID:-1000}; \
    if [ "$USERNAME_FINAL" != "vscode" ] && [ -n "$USERNAME_FINAL" ]; then \
        groupmod --new-name "$USERNAME_FINAL" vscode && \
        usermod --login "$USERNAME_FINAL" --home "/home/$USERNAME_FINAL" --move-home vscode && \
        if [ -f /etc/sudoers.d/vscode ]; then \
            mv /etc/sudoers.d/vscode "/etc/sudoers.d/$USERNAME_FINAL" && \
            sed -i "s/vscode/$USERNAME_FINAL/g" "/etc/sudoers.d/$USERNAME_FINAL"; \
        fi; \
    fi && \
    CURRENT_GID=$(id -g "$USERNAME_FINAL") && \
    CURRENT_UID=$(id -u "$USERNAME_FINAL") && \
    if [ "$TARGET_GID" != "$CURRENT_GID" ]; then \
        groupmod --gid "$TARGET_GID" "$USERNAME_FINAL" 2>/dev/null || true; \
    fi && \
    if [ "$TARGET_UID" != "$CURRENT_UID" ]; then \
        usermod --uid "$TARGET_UID" "$USERNAME_FINAL" && \
        find "/home/$USERNAME_FINAL" -maxdepth 5 -exec chown -h "$TARGET_UID" {} + 2>/dev/null || true; \
    fi
