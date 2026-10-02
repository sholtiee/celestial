#!/bin/bash
# Восстанавливает .mcsrc/ — ванильные исходники (для справки по API) и ресурсы игры (нужны генераторам ассетов).
#   .mcsrc/common  — исходники общей части (net/minecraft/...)
#   .mcsrc/client  — исходники клиентской части
#   .mcsrc/assets  — содержимое minecraft-client.jar (assets/ и data/ ванили)
set -e
cd "$(dirname "$0")/.."
export JAVA_HOME=${JAVA_HOME:-/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home}
./gradlew genSources --no-configuration-cache -q
mkdir -p .mcsrc/common .mcsrc/client .mcsrc/assets
unzip -qo "$(find .gradle/loom-cache -name 'minecraft-common-*-sources.jar' | head -1)" -d .mcsrc/common
unzip -qo "$(find .gradle/loom-cache -name 'minecraft-clientOnly-*-sources.jar' | head -1)" -d .mcsrc/client
unzip -qo ~/.gradle/caches/fabric-loom/26.3/minecraft-client.jar 'assets/*' 'data/*' -d .mcsrc/assets
echo ".mcsrc готов"
