import streamlit as st
import sqlite3
import random
import plotly.express as px
from contextlib import contextmanager
from streamlit.components.v1 import html

# Custom CSS and JavaScript injections
def inject_custom_resources():
    st.markdown("""
    <style>
    * { 
        font-family: 'Orbitron', sans-serif;
        transition: all 0.3s ease-in-out;
    }
    
    .book-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #4CAF50;
        color: dodgerblue !important;
    }
    
    .book-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    .header {
        animation: glowingExpand 1.5s ease-out;
    }

    @keyframes glowingExpand {
        0% { transform: scale(1); }
        100% { transform: scale(1.1); }
    }

    .book-card.glow::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        z-index: -1;
        border-radius: inherit;
        background: linear-gradient(45deg, #ff0057, #ff8500, #ff0057, #ff8500);
        background-size: 400%;
        filter: blur(8px);
        animation: glow 3s linear infinite;
    }

    @keyframes glow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stats-card {
        background: linear-gradient(45deg, #6C5CE7, #48DBFB);
        color: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .st-emotion-cache-1v0mbdj img {
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    </style>    
    """, unsafe_allow_html=True)
    
    st.markdown('<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400..900&display=swap" rel="stylesheet">', unsafe_allow_html=True)

inject_custom_resources()

# Database setup
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('library.db')
    try:
        yield conn
    finally:
        conn.close()

# Animated Header 
st.markdown("""
    <div class="text-center p-6" style="position: relative;">
        <h1 class="header text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-600 to-pink-600">
            📚 Personal Library Manager 
        </h1>
        <div class="absolute top-0 left-0 w-full h-full" id="particle-canvas"></div>
    </div>
""", unsafe_allow_html=True)


class Book:
    def __init__(self, title, author, publication_year, genre, read_status):
        self.title = title
        self.author = author
        self.publication_year = publication_year
        self.genre = genre
        self.read_status = read_status

    def card_html(self, index):
        status_emoji = "✅" if self.read_status else "📖"
        status_color = "text-green-500" if self.read_status else "text-yellow-500"
        return f"""
        <div class="book-card">
            <div class="flex items-center justify-between">
                <h3 class="text-xl font-bold text-gray-800">{self.title}</h3>
                <span class="{status_color} text-2xl">{status_emoji}</span>
            </div>
            <div class="mt-2 text-gray-600">
                <p>👤 {self.author}</p>
                <p>📅 {self.publication_year} | 🎭 {self.genre}</p>
            </div>
        </div>
        """

class Library:
    def __init__(self):
        self.create_table()

    def create_table(self):
        with get_db_connection() as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS books
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT NOT NULL,
                          author TEXT NOT NULL,
                          publication_year INTEGER,
                          genre TEXT,
                          read_status BOOLEAN)''')

    def add_book(self, book):
        with get_db_connection() as conn:
            conn.execute('''INSERT INTO books 
                         (title, author, publication_year, genre, read_status)
                         VALUES (?, ?, ?, ?, ?)''',
                         (book.title, book.author, book.publication_year, 
                          book.genre, book.read_status))
            conn.commit()

    def remove_book(self, title):
        with get_db_connection() as conn:
            conn.execute("DELETE FROM books WHERE title = ?", (title,))
            conn.commit()

    def search_books(self, search_by, query):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if search_by == "title":
                cursor.execute("SELECT * FROM books WHERE LOWER(title) LIKE ?", 
                             ('%' + query.lower() + '%',))
            elif search_by == "author":
                cursor.execute("SELECT * FROM books WHERE LOWER(author) LIKE ?", 
                             ('%' + query.lower() + '%',))
            return [Book(*row[1:]) for row in cursor.fetchall()]

    def display_books(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books")
            return [Book(*row[1:]) for row in cursor.fetchall()]

    def display_statistics(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books")
            total_books = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM books WHERE read_status = 1")
            read_books = cursor.fetchone()[0]
            
            percentage_read = (read_books / total_books) * 100 if total_books > 0 else 0
            return total_books, percentage_read

class EnhancedLibrary(Library):
    def genre_distribution(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT genre, COUNT(*) FROM books GROUP BY genre")
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def publication_timeline(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT publication_year, COUNT(*) FROM books GROUP BY publication_year")
            return {row[0]: row[1] for row in cursor.fetchall()}

def main():
    library = EnhancedLibrary()

    # Sidebar with animated menu
    with st.sidebar:
        menu = ["📖 Add a Book", "❌ Remove a Book", "🔍 Search for a Book", 
                "📚 Display All Books", "📊 Advanced Statistics", "📗 Recommend a Book"]
        choice = st.radio("Choose an action", menu, index=0, 
                        help="Select an option from the menu", key="menu_select")

    if choice == "📖 Add a Book":
        with st.form(key="add_book_form"):
            cols = st.columns(2)
            with cols[0]:
                title = st.text_input("📕 Book Title", help="Enter the book title")
                author = st.text_input("✍️ Author Name", help="Enter the author's name")
            with cols[1]:
                publication_year = st.number_input("📅 Publication Year", 
                                                 min_value=0, max_value=2024, step=1)
                genre = st.selectbox("🎭 Genre", ["Fiction", "Non-Fiction", "Sci-Fi", 
                                                  "Mystery", "Biography", "Other"])
            read_status = st.checkbox("✅ Mark as read", value=False)
            
            if st.form_submit_button("🚀 Add Book to Library", use_container_width=True):
                if title and author:
                    book = Book(title, author, publication_year, genre, read_status)
                    library.add_book(book)
                    st.success("🎉 Book added successfully!")
                    html("<script>triggerConfetti()</script>")
                else:
                    st.error("⚠️ Please fill in all required fields")

    elif choice == "❌ Remove a Book":
        st.markdown("### 🔥 Remove a Book")
        search_term = st.text_input("Search books to remove", key="remove_search")
        if search_term:
            results = library.search_books("title", search_term)
            if results:
                selected = st.selectbox("Select book to remove", 
                                       [book.title for book in results])
                if st.button("🗑️ Confirm Removal", type="primary"):
                    library.remove_book(selected)
                    st.success(f"Removed '{selected}' from library")
            else:
                st.warning("No matching books found")

    elif choice == "🔍 Search for a Book":
        st.markdown("### 🔎 Advanced Search")
        cols = st.columns(3)
        with cols[0]:
            search_by = st.selectbox("Search by", ["Title", "Author", "Genre"])
        with cols[1]:
            query = st.text_input(f"Enter {search_by.lower()}")
        with cols[2]:
            st.write("")
            st.write("")
            if st.button("🚀 Search Now"):
                results = library.search_books(search_by.lower(), query)
                if results:
                    st.markdown(f"**📚 Found {len(results)} matches:**")
                    for idx, book in enumerate(results):
                        st.markdown(book.card_html(idx), unsafe_allow_html=True)
                else:
                    st.warning("No books found matching your criteria")

    elif choice == "📚 Display All Books":
        st.markdown("### 📚 Your Personal Library")
        books = library.display_books()
        if books:
            cols = st.columns(3)
            for idx, book in enumerate(books):
                with cols[idx % 3]:
                    st.markdown(book.card_html(idx), unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="text-center py-8">
                    <div class="text-6xl mb-4">😢</div>
                    <h3 class="text-xl text-gray-500">Your library is empty!</h3>
                </div>
            """, unsafe_allow_html=True)

    elif choice == "📊 Advanced Statistics":
        st.markdown("### 📈 Library Insights")
        total, percentage = library.display_statistics()
        
        cols = st.columns(2)
        with cols[0]:
            st.markdown(f"""
                <div class="stats-card">
                    <h3 class="text-2xl font-bold">Total Books</h3>
                    <div class="text-4xl mt-2">{total}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with cols[1]:
            st.markdown(f"""
                <div class="stats-card">
                    <h3 class="text-2xl font-bold">Read Percentage</h3>
                    <div class="text-4xl mt-2">{percentage:.1f}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Genre Distribution Pie Chart
        genre_data = library.genre_distribution()
        if genre_data:
            fig = px.pie(values=list(genre_data.values()), names=list(genre_data.keys()),
                        title="📊 Genre Distribution", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)

    elif choice == "📗 Recommend a Book":
        st.markdown("### 🎯 Your Next Read")
        unread = [book for book in library.display_books() if not book.read_status]
        if unread:
            if st.button("✨ Generate Recommendation"):
                book = random.choice(unread)
                st.markdown(f"""
                    <div class="book-card glow">
                        <h3 class="text-2xl font-bold text-purple-600">We recommend:</h3>
                        <div class="mt-4">
                            <p class="text-xl">📖 {book.title}</p>
                            <p class="text-gray-600">👤 {book.author}</p>
                            <p class="text-sm text-gray-500">📅 {book.publication_year} | 🎭 {book.genre}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🎉 Congratulations! You've read all books in your library!")

if __name__ == "__main__":
    main()