# Setup

build:
	docker build -t scrapper_img .

up:
	docker run -t -d \
	-p 127.0.0.1:34617:34617/tcp \
	--name scrapper_cont \
	scrapper_img

build_up:
	make build
	make up

build_up_no_cache:
	docker build --no-cache -t scrapper_img .
	make up

# Run
## Product
run:
	docker exec -it scrapper_cont poetry run python src/scrapper/scrap.py $(url)

run_example_product_manual:
	@read -p "Enter URL: " url; \
	docker exec -it scrapper_cont poetry run python src/scrapper/scrap.py $$url

run_example_product_auto:
	# Call the category page and use the first item (if exists) as input for make run
	url=$$(docker exec -it scrapper_cont poetry run python src/test/get_link_first_product.py | tr -d '\r'); \
	if [ "$$url" != "No products found" ]; then \
		make run url="$$url"; \
	else \
		echo "No products found"; \
	fi

run_example_product:
	# Just to make this example more generic, it will be suitable to call to a category page and run the example with the first item (if exists)
	docker exec -it scrapper_cont poetry run python src/scrapper/scrap.py "https://en.gb.scalperscompany.com/products/65321-sccollar-bomber-jacket-ss26-red"

## Collection
run_example_collection:
	docker exec -it scrapper_cont poetry run python app/modules/get_all_products_from_collection.py $(url)

run_example_collection_manual:
	@read -p "Enter URL: " url; \
	docker exec -it scrapper_cont poetry run python app/modules/get_all_products_from_collection.py $$url

## Shop
run_example_shop:
	docker exec -it scrapper_cont poetry run python app/modules/get_all_products_from_shop.py

## Testing
run_tests:
	# Find and execute all .sh test files
	docker exec -it scrapper_cont poetry run bash tests/test__infra__get_last_price.sh
	# Run Python tests
	docker exec -it scrapper_cont poetry run python -m unittest discover -s tests

run_tests_no_docker:
	bash tests/test__infra__get_last_price.sh
	python3 -m unittest discover -s tests

# Down and remove
stop:
	docker stop scrapper_cont

rm_cont:
	docker rm scrapper_cont

rm_img:
	docker image rm scrapper_img

rm_all:
	make rm_cont
	make rm_img

stop_rm_all:
	make stop
	make rm_all

rebuild:
	make stop_rm_all
	make build

rebuild_and_up:
	make stop_rm_all
	make build_up

rebuild_and_up_no_cache:
	make stop_rm_all
	make build_up_no_cache

# ============================================================================
# Local Development Commands (without Docker)
# ============================================================================

# Scrape a single product
scrape-product:
	python3 -m src.scrapper.scrap $(url)

# Get all product links from a collection
scrape-collection-links:
	python3 -m src.links_getter.get_product_links_from_page $(url)

# Get all collections from shop
scrape-collections:
	python3 -m src.links_getter.get_all_collection_links

# Get first product link from shop
scrape-first-product:
	python3 -m src.test.get_link_first_product

# Scrape all products from a collection (SLOW - may take hours)
scrape-collection-products:
	python3 -m app.modules.get_all_products_from_collection $(url)

# Scrape all products from entire shop (VERY SLOW - may take days)
scrape-shop-products:
	python3 -m app.modules.get_all_products_from_shop

# Run all tests
test:
	python3 -m unittest discover -s tests -v
