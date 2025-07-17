# Подготовка рабочей среды
## Установка рабочего окружения на Ubuntu 22.04
### 1. Установка python3 и pip
```
DEBIAN_FRONTEND=noninteractive apt update
DEBIAN_FRONTEND=noninteractive apt install -y python3 python3-pip python3-venv
```

### 2. Добавление alias (перенаправим python → python3, и pip → pip3)
```
echo "alias python='python3'" >> ~/.bashrc
echo "alias pip='pip3'" >> ~/.bashrc
source ~/.bashrc
```

### 3. Проверка
```
python --version
pip --version
```

### 4. Создание виртуального окружения
```
python -m venv ~/llm
source ~/llm/bin/activate
```

### 5. Установка зависимостей (базовый стек)
Скачивание файла `requirements.txt`
```
curl -o requirements.txt https://gist.githubusercontent.com/mbps54/f4b7ebd73b157aa1dfef86c4d7be4279/raw/a3ecde01acda80b149cf01d46450ed5856cca003/requirements.txt
```
Установка ПО
```
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Экспорт API ключа
```
 export OPENAI_API_KEY=sk-proj-<...>
```
