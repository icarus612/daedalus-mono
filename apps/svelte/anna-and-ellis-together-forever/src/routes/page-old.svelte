<script>
	import { DateCard, FancyImageSection, BasicImageSection } from '$components';
</script>

<div class="flex w-full justify-center content-center px-10 py-20">
	<div class="basis-1/2 basis-1/3 px-20">
		<h1
			class="font-light text-9xl bg-gradient-to-br from-gray-600 via-gray-200 to-white inline-block text-transparent bg-clip-text"
		>
			Anna <br />
			&amp; <br />
			Ellis
		</h1>
    <h2 class="text-2xl font-bold">Together Forever</h2>
	</div>
	<div class="basis-2/3">
		<!-- Main content -->
		<div class="flex justify-center space-x-10">
			<!-- Image cards -->
			<DateCard
				imgSrc="first-date.jpg"
				imgText="01"
				header="12 MAR 2022"
				subHeader="THE FIRST DATE"
			/>
			<DateCard
				imgSrc="engagement.jpg"
				imgText="02"
				header="07 MAY 2023"
				subHeader="THE ENGAGEMENT"
			/>
			<DateCard
				imgSrc="forever-journey.jpg"
				imgText="03"
				header="24 SEP 2023"
				subHeader="THE FOREVER JOURNEY"
			/>
		</div>
	</div>
</div>

<BasicImageSection
	header="The First Date"
	subHeader="March 12, 2022"
	img={{
		src: "first-date.jpg",
		alt: "First date piture"
	}}/>

<BasicImageSection
	header="The Engagement"
	subHeader="May 7, 2023"
	img={{
		src: "engagement.jpg",
		alt: "Engagement piture"
	}}
	reversed={true}
	text="
		At the scenic beach and botanical gardens, 
		a memorable engagement unfolded. 
		Amidst the peaceful ocean sounds and surrounded by the vibrant flora of the gardens, 
		a special moment was shared. 
		This setting provided the perfect backdrop for the beginning of a new chapter, 
		capturing the essence of a beautiful journey ahead. 
		The day was marked by natural beauty and a sense of joyful anticipation, 
		creating a lasting memory for all.
	"
/>

<FancyImageSection
	header="The Forever Journey"
	subHeader="September 24, 2023"
	imageGroupContent={{ width: "200px" }}
	text="
		Nestled in the picturesque surroundings of Treehouse Vineyards, 
		the setting is perfect for a wedding that blends romance with the serene beauty of nature. 
		With rows of verdant grapevines creating a stunning backdrop, 
		the vineyard provides a peaceful and romantic ambiance. 
		The soft afternoon light gently bathes the landscape, 
		adding a magical glow to the ceremony. 
		It's a place where laughter and heartfelt moments naturally come together, 
		surrounded by the simplicity and elegance of the vineyards. 
		Each wedding at Treehouse Vineyards is more than just an event; 
		it was an enchanting experience, 
		leaving lasting memories for all who attend.
	"
/>
