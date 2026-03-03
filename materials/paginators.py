from rest_framework.pagination import PageNumberPagination

class CoursePaginator(PageNumberPagination):
    """
    Пагинация для списка курсов
    """
    page_size = 5  # Количество элементов на странице
    page_size_query_param = 'page_size'  # Параметр для изменения количества элементов
    max_page_size = 50  # Максимальное количество элементов на странице
    page_query_param = 'page'  # Параметр для номера страницы

class LessonPaginator(PageNumberPagination):
    """
    Пагинация для списка уроков
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    page_query_param = 'page'