# Usar la imagen base oficial de Python
FROM python:3.11

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo requirements.txt al contenedor
COPY requirements.txt .

# Instalar las dependencias de la aplicación
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación al contenedor
COPY . .

# Exponer el puerto en el que la aplicación escuchará (por defecto, FastAPI usa el puerto 8000)
#EXPOSE 8000

# Comando para ejecutar FastAPI usando Uvicorn
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
