import pandas as pd
import scipy.sparse as sp
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def map_user_score(row):
    try:
        if row['click'] > -1 and row['basket'] > -1 and row['order'] > -1:
            return (row['click'] * 1) + (row['basket'] * 10) + (row['order'] * 20)
        return 0
    except:
        return 0


transactions_df = pd.read_csv('./dataset/transactions.csv', sep="|", error_bad_lines=False)
transactions_df['user_score'] = transactions_df.apply(map_user_score, axis=1)
transactions_df = transactions_df.drop(columns=['sessionID', 'click', 'basket', 'order'])
transactions_df = transactions_df.groupby('itemID').sum()
transactions_df.head()


def get_item_score(item):
    try:
        score = int(transactions_df.loc[item.itemID])
        item.score = score
        return item
    except:
        return item


def get_data():
    items_data = pd.read_csv('./dataset/items.csv', sep="|", error_bad_lines=False)
    items_data = items_data.dropna(how='any')  # change later
    items_data['title'] = items_data['title'].str.lower()
    #     return items_data.drop_duplicates(subset='title', keep='first').head(40000)
    items_data = items_data.drop_duplicates(subset='title', keep='first')
    #     items_data = items_data.loc[items_data["subtopics"] != '[]']
    items_data['score'] = 0

    items_data = items_data.apply(get_item_score, axis=1)
    items_data = items_data.reset_index(drop=True)
    return items_data.head(40000)


# get_data().head()  # 78029 without returning head


def combine_data(data):
    data_recommend = data.drop(columns=['itemID', 'title', 'publisher', 'subtopics'])
    # we use author, publisher, main topic
    data_recommend['combine'] = data_recommend[data_recommend.columns[0:2]].apply(
        lambda x: ' '.join(x.dropna().astype(str)), axis=1)
    data_recommend = data_recommend.drop(columns=['author', 'main topic'])
    data_recommend['combine'] = data_recommend['combine'].replace({"[^A-Za-z0-9 ]+": ""}, regex=True)
    return data_recommend


combined = combine_data(get_data())


def transform_data(data_combine, data_plot):
    count = CountVectorizer(stop_words='english')
    count_matrix = count.fit_transform(data_combine['combine'])

    #     tfidf = TfidfVectorizer(stop_words='english')
    #     tfidf_matrix = tfidf.fit_transform(data_plot['subtopics'])

    #     combine_sparse = sp.hstack([count_matrix, tfidf_matrix], format='csr')

    count2 = CountVectorizer(stop_words='english')
    count_matrix2 = count2.fit_transform(data_plot['subtopics'].apply(lambda x: x[1:-1].replace(',', ' ')))
    combine_sparse = sp.hstack([count_matrix, count_matrix2], format='csr')

    cosine_sim = cosine_similarity(combine_sparse, combine_sparse)

    #     cosine_sim = cosine_similarity(count_matrix)

    return cosine_sim


# data = get_data()
# pd.Series(data.index, index=data['title'])['red queen 1'] # 2
def recommend_books(title, data, combine, transform):
    indices = pd.Series(data.index, index=data['title'])
    index = indices[title]

    sim_scores = list(enumerate(transform[index]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]

    book_indices = [i[0] for i in sim_scores]
    #     print(book_indices)

    book_id = data['itemID'].iloc[book_indices]
    book_title = data['title'].iloc[book_indices]
    book_author = data['author'].iloc[book_indices]
    book_main_topic = data['main topic'].iloc[book_indices]
    book_scores = data['score'].iloc[book_indices]
    book_subtopics = data['subtopics'].iloc[book_indices]

    recommendation_data = pd.DataFrame(columns=['Book_Id', 'Name', 'Author'])

    recommendation_data['Book_Id'] = book_id
    recommendation_data['Name'] = book_title
    recommendation_data['Author'] = book_author
    recommendation_data['Main Topic'] = book_main_topic
    recommendation_data['Subtopics'] = book_subtopics
    recommendation_data['Score'] = book_scores

    return recommendation_data


def results(book_name, find_book, combine_result, transform_result, sort_by_score=False):
    book_name = book_name.lower()

    # find_book = get_data()
    # combine_result = combine_data(find_book)
    # transform_result = transform_data(combine_result,find_book)

    if book_name not in find_book['title'].unique():
        return 'Book not in Database'

    else:
        recommendations = recommend_books(book_name, find_book, combine_result, transform_result)
        if (sort_by_score):
            return recommendations.sort_values(by=['Score'], ascending=False)
        else:
            return recommendations


#             return recommendations.to_dict('records')
global find_book
find_book = get_data()
global combine_result
combine_result = combined
global transform_result
transform_result = transform_data(combine_result, find_book)

# from numpy import save
# save('transform_result.npy', transform_result)
# from numpy import load
# transformed_result = load('transform_result.npy')
# filename = 'transform_result.npz'
# from numpy import savez_compressed
# savez_compressed(filename, transform_result)
# filename = 'transform_result.npz'
# from numpy import load
# loaded = load(filename)
# transform_result = loaded['arr_0']
def find_book_by_title(title):
    return find_book[find_book['title'] == title].loc[:, ['title', 'author', 'main topic', 'score']]


def get_recommendations_for(title, sort_by_score=True):
    return results(title, find_book, combine_result, transform_result, sort_by_score)


# find_book_by_title('red queen 1')
# get_recommendations_for('Red Queen 1')
# find_book_by_title('red queen 2. glass sword')
# get_recommendations_for('red queen 2. glass sword')
# find_book_by_title('the darkest part of the forest')
# get_recommendations_for('the darkest part of the forest')
