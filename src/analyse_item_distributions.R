###
#
# Creation of graphics for the mythic and legendary distribution
#
###


###
# Define constants
FOLDER_DATA <- 'data/'
FOLDER_ICONS <- 'icons/'
FOLDER_IMAGES <- 'images/'

MYTHIC_DATA_FILE <- 'mythics_%s_%s_%s.csv'
LEGENDARY_MYTHIC_DATA_FILE <- 'legendary_and_mythics_%s_%s_%s.csv'
MYTHIC_IDS <- 'mythic_ids.csv'
CHAMPION_IDS <- 'champion_ids.csv'

MYTHIC_CHAMPION_N <- 'mythic_champions_n/'

REGION <- 'euw1'
EARLIEST_DATE_FOR_GAMES <- '20210428'
LATEST_DATE_FOR_GAMES <- '20210511'

MIN_OCCURENCE_MYTHICS <- 10

MAPPING_QUEUE_ID <- list(c('400', '420', '440', '450'), c('Normal', 'Ranked', 'Flex', 'ARAM'))


###
# Load packages
pakete <- c('data.table', 'RColorBrewer', 'png', 'gplots')

for (paket in pakete) {
    library(paket, character.only = TRUE)
    rm(paket)
}
rm(pakete)


###
# Import data
mythicData <- fread(file = sprintf('%s%s', FOLDER_DATA, sprintf(MYTHIC_DATA_FILE,
    REGION, EARLIEST_DATE_FOR_GAMES, LATEST_DATE_FOR_GAMES)))

legendaryAndMythicData <- fread(file = sprintf('%s%s', FOLDER_DATA, sprintf(LEGENDARY_MYTHIC_DATA_FILE,
    REGION, EARLIEST_DATE_FOR_GAMES, LATEST_DATE_FOR_GAMES)))

mythicItems <- fread(file = sprintf('%s%s', FOLDER_DATA, MYTHIC_IDS))

championInformation <- fread(file = sprintf('%s%s', FOLDER_DATA, CHAMPION_IDS))

championIcons <- list()
itemIcons <- list()

for (file in list.files(path = sprintf('%s%s', FOLDER_DATA, FOLDER_ICONS))) {
    if ((fileId <- substr(file, 1, nchar(file)-4)) %in% championInformation[['IdName']]) {
        # Champions
        championIcons[[as.character(championInformation[championInformation[['IdName']] == fileId, Id])
            ]] <- readPNG(sprintf('%s%s%s', FOLDER_DATA, FOLDER_ICONS, file))
    } else {
        # Items
        itemIcons[[fileId]] <- readPNG(sprintf('%s%s%s', FOLDER_DATA, FOLDER_ICONS, file))
    }
}


###
# Create a color palette for the items
mythicItemsColorPalette <- rgb(colorRamp(
    brewer.pal(11, 'Spectral'))((0:dim(mythicItems)[1]) / dim(mythicItems)[1]) / 255)

# Add None as a mythic item
mythicItems <- rbindlist(list(mythicItems, data.table(Id = 0, Item = 'None')))


###
# Count number of mythic items for each champion and queue.
# Only consider champions with at least 200 occurences for every queue
championOccurrences <- mythicData[, .N, .(Champion, Queue)][, min(N), .(Champion)]
championsToKeepForMythicAnalysis <- championOccurrences[V1 >= MIN_OCCURENCE_MYTHICS, Champion]

mythicDataForSelectedChampions <- mythicData[mythicData[['Champion']] %in% championsToKeepForMythicAnalysis,]

# Group data by queue and champion
mythicDataForSelectedChampions <- mythicDataForSelectedChampions[, .N, .(Champion, Queue, Mythic)]


###
# Mythicplots for all champions seperately
nLegendItemsPerRow <- 8
legendWidth <- 4
legendWidthIconScale <- 5/6
legendItemInsetX <- 1/2
legendItemInsetY <- 1/10

scaleImageX <- 1/14
scaleImageY <- 1/8
yTitleOffset <- 1/50

legendScaleX <- 1 / 40
legendScaleY <- 1 / 8
legendOffsetY <- 1 / 20

pb <- txtProgressBar(min = 1, max = length(championsToKeepForMythicAnalysis), style = 3)
ct <- 1
for (championId in championsToKeepForMythicAnalysis) {
    mythicDataForChampion <- mythicDataForSelectedChampions[Champion == championId,]
    mythicDataAsMatrixForChampion <- dcast(mythicDataForChampion, Mythic ~ Queue, value.var = 'N')
    mythicDataAsMatrixForChampion[is.na(mythicDataAsMatrixForChampion)] <- 0

    # Order on sum
    mythicDataAsMatrixForChampion <- mythicDataAsMatrixForChampion[
        order(-rowSums(mythicDataAsMatrixForChampion[, -"Mythic", with = FALSE]))]


    colorIndex <- unlist(sapply(mythicDataAsMatrixForChampion[['Mythic']], function(x) which(x == mythicItems[['Id']])))
    colorSelection <- mythicItemsColorPalette[colorIndex]

    # Create matrix for barplot
    championMythicMatrix <- as.matrix(mythicDataAsMatrixForChampion[, -"Mythic", with = FALSE])
    matrixColNames <- colnames(championMythicMatrix)
    for (j in 1:4) {
        matrixColNames <- replace(matrixColNames, matrixColNames == MAPPING_QUEUE_ID[[1]][j],
            MAPPING_QUEUE_ID[[2]][j])
    }
    colnames(championMythicMatrix) <- matrixColNames

    nLegendItemsRows <- (dim(mythicDataAsMatrixForChampion)[1] - 1) %/% nLegendItemsPerRow + 1


    # Barplot with absolute numbers
    png(sprintf('%s%s%s_%s_%s.png', FOLDER_IMAGES, MYTHIC_CHAMPION_N,
        championInformation[championInformation[['Id']] == championId, 'IdName'], 'counts', REGION),
        width = 800 + 40 * nLegendItemsRows, height = 700, res = 110)

    par(xpd = TRUE, mar = c(3, 3, 4, 1 + nLegendItemsRows * legendWidth * 3 / 4))
    barplot(championMythicMatrix, col = colorSelection)

    usr <- par('usr')
    xMid <- (xLen <- (usr[2] - usr[1])) / 2
    yLen <- usr[4] - usr[3]

    legendIconDx <- xLen / nLegendItemsPerRow * legendWidthIconScale
    legendIconDy <- yLen / nLegendItemsPerRow * legendWidthIconScale

    # Title image
    rasterImage(championIcons[[as.character(championId)]],
        xleft = xMid - xLen * scaleImageX, ybottom = usr[4] + yLen * yTitleOffset,
        xright = xMid + xLen * scaleImageX, ytop = usr[4] + yLen * (scaleImageY + yTitleOffset))

    # Legend items
    for (j in 1:dim(mythicDataAsMatrixForChampion)[1]) {
        xPos <- 1 + ((j-1) %/% nLegendItemsPerRow) * legendWidth

        # Background rectangle
        rect(xleft = usr[2] + xPos * xLen * legendScaleX,
            ybottom = usr[3] + ((j-1) %% nLegendItemsPerRow + legendOffsetY) * yLen * legendScaleY,
            xright = usr[2] + (xPos + legendWidth * legendWidthIconScale) * xLen * legendScaleX,
            ytop = usr[3] + (((j-1) %% nLegendItemsPerRow + legendOffsetY) + legendWidthIconScale) * yLen * legendScaleY, col = colorSelection[j])

        # Item icon
        if ((itemId <- mythicDataAsMatrixForChampion[j, Mythic]) != 0) {
            rasterImage(itemIcons[[as.character(itemId)]],
                xleft = usr[2] + (xPos + legendItemInsetX) * xLen * legendScaleX,
                ybottom = usr[3] + ((j-1) %% nLegendItemsPerRow + legendOffsetY + legendItemInsetY) * yLen * legendScaleY,
                xright = usr[2] + (xPos - legendItemInsetX + legendWidth * legendWidthIconScale) * xLen * legendScaleX,
                ytop = usr[3] + (((j-1) %% nLegendItemsPerRow + legendOffsetY - legendItemInsetY) + legendWidthIconScale) * yLen * legendScaleY
            )
        }
    }

    dev.off()

    ###
    # Same plot but with frequencies instead of absolute counts
    championMythicMatrixFrequencies <- t(t(championMythicMatrix) / apply(championMythicMatrix, 2, sum))

    png(sprintf('%s%s%s_%s_%s.png', FOLDER_IMAGES, MYTHIC_CHAMPION_N,
        championInformation[championInformation[['Id']] == championId, 'IdName'], 'frequency', REGION),
        width = 800 + 40 * nLegendItemsRows, height = 700, res = 110)

    par(xpd = TRUE, mar = c(3, 3, 4, 1 + nLegendItemsRows * legendWidth * 3 / 4))
    barplot(championMythicMatrixFrequencies, col = colorSelection)

    usr <- par('usr')
    xMid <- (xLen <- (usr[2] - usr[1])) / 2
    yLen <- usr[4] - usr[3]

    legendIconDx <- xLen / nLegendItemsPerRow * legendWidthIconScale
    legendIconDy <- yLen / nLegendItemsPerRow * legendWidthIconScale

    # Title image
    rasterImage(championIcons[[as.character(championId)]],
        xleft = xMid - xLen * scaleImageX, ybottom = usr[4] + yLen * yTitleOffset,
        xright = xMid + xLen * scaleImageX, ytop = usr[4] + yLen * (scaleImageY + yTitleOffset))

    # Legend items
    for (j in 1:dim(mythicDataAsMatrixForChampion)[1]) {
        xPos <- 1 + ((j-1) %/% nLegendItemsPerRow) * legendWidth

        # Background rectangle
        rect(xleft = usr[2] + xPos * xLen * legendScaleX,
            ybottom = usr[3] + ((j-1) %% nLegendItemsPerRow + legendOffsetY) * yLen * legendScaleY,
            xright = usr[2] + (xPos + legendWidth * legendWidthIconScale) * xLen * legendScaleX,
            ytop = usr[3] + (((j-1) %% nLegendItemsPerRow + legendOffsetY) + legendWidthIconScale) * yLen * legendScaleY, col = colorSelection[j])

        # Item icon
        if ((itemId <- mythicDataAsMatrixForChampion[j, Mythic]) != 0) {
            rasterImage(itemIcons[[as.character(itemId)]],
                xleft = usr[2] + (xPos + legendItemInsetX) * xLen * legendScaleX,
                ybottom = usr[3] + ((j-1) %% nLegendItemsPerRow + legendOffsetY + legendItemInsetY) * yLen * legendScaleY,
                xright = usr[2] + (xPos - legendItemInsetX + legendWidth * legendWidthIconScale) * xLen * legendScaleX,
                ytop = usr[3] + (((j-1) %% nLegendItemsPerRow + legendOffsetY - legendItemInsetY) + legendWidthIconScale) * yLen * legendScaleY
            )
        }
    }

    dev.off()



    ct <- ct + 1
    setTxtProgressBar(pb, ct)
}
close(pb)


###
# Create a champion occurence frequency heatmap by queue -> ARAM champions?
queueOccurenceData <- mythicDataForSelectedChampions[, sum(N), by = .(Champion, Queue)]
queueOccurenceData <- dcast(queueOccurenceData, Queue ~ Champion, value.var = 'V1')
queueOccurenceData[is.na(queueOccurenceData)] <- 0

queueOccurenceMatrix <- as.matrix(queueOccurenceData)[, -1]

matrixRowNames <- queueOccurenceData[['Queue']]
for (j in 1:4) {
    matrixRowNames <- replace(matrixRowNames, matrixRowNames == MAPPING_QUEUE_ID[[1]][j],
        MAPPING_QUEUE_ID[[2]][j])
}

rownames(queueOccurenceMatrix) <- matrixRowNames

queueOccurenceMatrix <- t(t(queueOccurenceMatrix) / apply(queueOccurenceMatrix, 2, sum))

lmat <- rbind(c(5,3,4), c(2,1,4))
lhei <- c(1.5, 4)
lwid <- c(1, 50, 5)

xStartHeatmapIcons <- -0.0065
xDeltaHeatmapIcons <- 0.00584
xImageHeatmapIcons <- 0.01

yStartHeatmapIcons <- -0.053
yDeltaHeatmapIcons <- -0.026
yImageHeatmapIcons <- 0.025

nColorsHeatmap <- 51
colorsForHeatmap <- rgb(colorRamp(
    brewer.pal(11, 'RdYlGn'))((0:(nColorsHeatmap-1)) / (nColorsHeatmap-1)) / 255)

png(sprintf('%s%s_%s.png', FOLDER_IMAGES, 'heatmap_queue_types_comparison' , REGION), width = 4000, height = 1600, res = 110)
htmp <- heatmap.2(queueOccurenceMatrix, dendrogram = 'column', density.info = 'none', trace = 'none', key = FALSE,
    lmat = lmat, lhei = lhei, lwid = lwid, col = colorsForHeatmap, scale = 'row', labCol = FALSE,
    hclustfun = function(x) hclust(x, method = 'ward.D2'), Rowv = FALSE)

par(xpd = TRUE)
championIds <- colnames(queueOccurenceMatrix)
for (i in 1:length(htmp[['colInd']])) {
    rasterImage(championIcons[[championIds[htmp[['colInd']][i]]]],
        xleft = xStartHeatmapIcons + (i - 1) * xDeltaHeatmapIcons,
        ybottom = yStartHeatmapIcons + ((i - 1) %% 2) * yDeltaHeatmapIcons,
        xright = xStartHeatmapIcons + (i - 1) * xDeltaHeatmapIcons + xImageHeatmapIcons,
        ytop = yStartHeatmapIcons + ((i - 1) %% 2) * yDeltaHeatmapIcons + yImageHeatmapIcons)
}

dev.off()

png(sprintf('%s%s_%s.png', FOLDER_IMAGES, 'heatmap_queue_types_frequencies' , REGION), width = 4000, height = 1600, res = 110)
htmp <- heatmap.2(queueOccurenceMatrix, dendrogram = 'column', density.info = 'none', trace = 'none', key = FALSE,
    lmat = lmat, lhei = lhei, lwid = lwid, col = colorsForHeatmap, labCol = FALSE,
    hclustfun = function(x) hclust(x, method = 'ward.D2'), Rowv = FALSE)

par(xpd = TRUE)
championIds <- colnames(queueOccurenceMatrix)
for (i in 1:length(htmp[['colInd']])) {
    rasterImage(championIcons[[championIds[htmp[['colInd']][i]]]],
        xleft = xStartHeatmapIcons + (i - 1) * xDeltaHeatmapIcons,
        ybottom = yStartHeatmapIcons + ((i - 1) %% 2) * yDeltaHeatmapIcons,
        xright = xStartHeatmapIcons + (i - 1) * xDeltaHeatmapIcons + xImageHeatmapIcons,
        ytop = yStartHeatmapIcons + ((i - 1) %% 2) * yDeltaHeatmapIcons + yImageHeatmapIcons)
}

dev.off()


###
# Create a mythic heatmap (separate for each queue type)
nColorsHeatmap <- 51
colorsForHeatmap <- rgb(colorRamp(
    brewer.pal(11, 'RdYlGn'))((0:(nColorsHeatmap-1)) / (nColorsHeatmap-1)) / 255)

lmat <- rbind(c(5,3,4), c(2,1,4))
lhei <- c(1.5, 4)
lwid <- c(1, 50, 2)


xStartHeatmapIcons <- -0.005
xDeltaHeatmapIcons <- 0.006175
xImageHeatmapIcons <- 0.01

yStartHeatmapIcons <- -0.051
yDeltaHeatmapIcons <- -0.028
yImageHeatmapIcons <- 0.025

xStartItemIcons <- 0.96
xImageTtemIcons <- 0.01

yStartItemIcons <- -0.025
yDeltaItemIcons <- 0.03245
yImageItemIcons <- 0.028


queueTypeMythicOccurrenceMatrices <- list()
for (i in 1:length(MAPPING_QUEUE_ID[[1]])) {
    queueId <- MAPPING_QUEUE_ID[[1]][i]

    # Select relevant data
    mythicOccurenceData <- mythicDataForSelectedChampions[Queue == as.integer(queueId), .(Champion, Mythic, N)]
    mythicOccurenceData <- dcast(mythicOccurenceData, Mythic ~ Champion, value.var = 'N')
    mythicOccurenceData[is.na(mythicOccurenceData)] <- 0

    mythicOccurenceData <- mythicOccurenceData[order(mythicOccurenceData[['Mythic']]),]

    mythicOccurenceMatrix <- as.matrix(mythicOccurenceData)[, -1]
    rownames(mythicOccurenceMatrix) <- mythicOccurenceData[['Mythic']]

    mythicOccurenceMatrix <- t(t(mythicOccurenceMatrix) / apply(mythicOccurenceMatrix, 2, sum))


    ###
    # Draw heatmap
    png(sprintf('%s%s_%s_%s.png', FOLDER_IMAGES, 'heatmap_mythics_frequencies', tolower(MAPPING_QUEUE_ID[[2]][i]), REGION), width = 4000, height = 1600, res = 110)

    htmp <- heatmap.2(mythicOccurenceMatrix, Rowv = FALSE, dendrogram = 'column', density.info = 'none',
        trace = 'none', key = FALSE,
        lmat = lmat, lhei = lhei, lwid = lwid, col = colorsForHeatmap, labCol = FALSE, labRow = FALSE,
        hclustfun = function(x) hclust(x, method = 'ward.D2'), sepcolor = 'black',
        colsep = 1:(dim(mythicOccurenceMatrix)[2] - 1), rowsep = 1:(dim(mythicOccurenceMatrix)[1] - 1))

    par(xpd = TRUE)
    championIds <- colnames(mythicOccurenceMatrix)
    for (j in 1:length(htmp[['colInd']])) {
        rasterImage(championIcons[[championIds[htmp[['colInd']][j]]]],
            xleft = xStartHeatmapIcons + (j - 1) * xDeltaHeatmapIcons,
            ybottom = yStartHeatmapIcons + ((j - 1) %% 2) * yDeltaHeatmapIcons,
            xright = xStartHeatmapIcons + (j - 1) * xDeltaHeatmapIcons + xImageHeatmapIcons,
            ytop = yStartHeatmapIcons + ((j - 1) %% 2) * yDeltaHeatmapIcons + yImageHeatmapIcons)
    }

    itemIds <- rownames(mythicOccurenceMatrix)
    for (j in 1:length(htmp[['rowInd']])) {
        if (itemIds[htmp[['rowInd']][j]] != "0") {
            rasterImage(itemIcons[[itemIds[htmp[['rowInd']][j]]]],
                xleft = xStartItemIcons,
                ybottom = yStartItemIcons + (j - 1) * yDeltaItemIcons,
                xright = xStartItemIcons + xImageTtemIcons,
                ytop = yStartItemIcons + (j - 1) * yDeltaItemIcons + yImageItemIcons)
        }
    }

    dev.off()

    # Save the matrices for comparisons
    queueTypeMythicOccurrenceMatrices[[MAPPING_QUEUE_ID[[2]][i]]] <- mythicOccurenceMatrix
}


##
# Compare Ranked to Normals
diffNormalsToRankedMythicsMatrix <- queueTypeMythicOccurrenceMatrices[['Normal']] - queueTypeMythicOccurrenceMatrices[['Ranked']]

# Draw heatmap
png(sprintf('%s%s_%s.png', FOLDER_IMAGES, 'heatmap_mythics_diff_frequencies_normals_ranked', REGION), width = 4000, height = 1600, res = 110)

htmp <- heatmap.2(diffNormalsToRankedMythicsMatrix, Rowv = FALSE, dendrogram = 'column', density.info = 'none',
    trace = 'none', key = FALSE,
    lmat = lmat, lhei = lhei, lwid = lwid, col = colorsForHeatmap, labCol = FALSE, labRow = FALSE,
    hclustfun = function(x) hclust(x, method = 'ward.D2'), sepcolor = 'black',
    colsep = 1:(dim(diffNormalsToRankedMythicsMatrix)[2] - 1), rowsep = 1:(dim(diffNormalsToRankedMythicsMatrix)[1] - 1))

par(xpd = TRUE)
championIds <- colnames(diffNormalsToRankedMythicsMatrix)
for (j in 1:length(htmp[['colInd']])) {
    rasterImage(championIcons[[championIds[htmp[['colInd']][j]]]],
        xleft = xStartHeatmapIcons + (j - 1) * xDeltaHeatmapIcons,
        ybottom = yStartHeatmapIcons + ((j - 1) %% 2) * yDeltaHeatmapIcons,
        xright = xStartHeatmapIcons + (j - 1) * xDeltaHeatmapIcons + xImageHeatmapIcons,
        ytop = yStartHeatmapIcons + ((j - 1) %% 2) * yDeltaHeatmapIcons + yImageHeatmapIcons)
}

itemIds <- rownames(diffNormalsToRankedMythicsMatrix)
for (j in 1:length(htmp[['rowInd']])) {
    if (itemIds[htmp[['rowInd']][j]] != "0") {
        rasterImage(itemIcons[[itemIds[htmp[['rowInd']][j]]]],
            xleft = xStartItemIcons,
            ybottom = yStartItemIcons + (j - 1) * yDeltaItemIcons,
            xright = xStartItemIcons + xImageTtemIcons,
            ytop = yStartItemIcons + (j - 1) * yDeltaItemIcons + yImageItemIcons)
    }
}

dev.off()


##
# Compare Ranked to ARAM
diffAramToRankedMythicsMatrix <- queueTypeMythicOccurrenceMatrices[['ARAM']] - queueTypeMythicOccurrenceMatrices[['Ranked']]

# Draw heatmap
png(sprintf('%s%s_%s.png', FOLDER_IMAGES, 'heatmap_mythics_diff_frequencies_aram_ranked', REGION), width = 4000, height = 1600, res = 110)

htmp <- heatmap.2(diffAramToRankedMythicsMatrix, Rowv = FALSE, dendrogram = 'column', density.info = 'none',
    trace = 'none', key = FALSE,
    lmat = lmat, lhei = lhei, lwid = lwid, col = colorsForHeatmap, labCol = FALSE, labRow = FALSE,
    hclustfun = function(x) hclust(x, method = 'ward.D2'), sepcolor = 'black',
    colsep = 1:(dim(diffAramToRankedMythicsMatrix)[2] - 1), rowsep = 1:(dim(diffAramToRankedMythicsMatrix)[1] - 1))

par(xpd = TRUE)
championIds <- colnames(diffAramToRankedMythicsMatrix)
for (j in 1:length(htmp[['colInd']])) {
    rasterImage(championIcons[[championIds[htmp[['colInd']][j]]]],
        xleft = xStartHeatmapIcons + (j - 1) * xDeltaHeatmapIcons,
        ybottom = yStartHeatmapIcons + ((j - 1) %% 2) * yDeltaHeatmapIcons,
        xright = xStartHeatmapIcons + (j - 1) * xDeltaHeatmapIcons + xImageHeatmapIcons,
        ytop = yStartHeatmapIcons + ((j - 1) %% 2) * yDeltaHeatmapIcons + yImageHeatmapIcons)
}

itemIds <- rownames(diffAramToRankedMythicsMatrix)
for (j in 1:length(htmp[['rowInd']])) {
    if (itemIds[htmp[['rowInd']][j]] != "0") {
        rasterImage(itemIcons[[itemIds[htmp[['rowInd']][j]]]],
            xleft = xStartItemIcons,
            ybottom = yStartItemIcons + (j - 1) * yDeltaItemIcons,
            xright = xStartItemIcons + xImageTtemIcons,
            ytop = yStartItemIcons + (j - 1) * yDeltaItemIcons + yImageItemIcons)
    }
}

dev.off()
